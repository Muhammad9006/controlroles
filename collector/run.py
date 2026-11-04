"""Collect jobs from every enabled employer, keep the relevant GCC roles, and write the site's data.

    python -m collector.run            # live run (needs internet)
    python -m collector.run --replay tests/fixtures   # offline run from saved responses

Outputs:
    site/jobs.js        data the website reads
    data/jobs.json      same data, for anything else
    data/state.json     when each job was first seen (keeps 'new' badges accurate between runs)
    data/run-report.md  what worked, what failed, and what to fix
"""
import argparse
import datetime
import json
import os
import sys

from .classify import clean_title, country_of, discipline_of, level_of
from .countries import CITIES, EXCLUDED_COUNTRIES, region_of
from .connectors import SYSTEMS, DESCRIBE
from . import facts, manual, reqlines, skills
KEEP_KEYS = ("sk", "yrs", "yrsMax", "deg", "skChecked", "elig", "sector", "pay", "ben", "leave", "rq", "locNote", "fx", "fxChecked", "fxV")  # what a posting read gives; carried forward between runs
FACTS_VERSION = 4  # raise when facts.py learns something new, so postings are read again
from .http import get_json
from .ids import job_id

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REAL_ROOT = ROOT
KEEP_FAILED_DAYS = 3  # if an employer's site fails, keep its last jobs this long before dropping them
KEEP_UNCONNECTED_DAYS = 21  # jobs imported by hand for employers with no connector yet stay this long after their last check
MAX_DESCRIBE_PER_RUN = 300  # postings read in full per employer per run (the rest are read on later runs)
MAX_POSTED_DAYS = 90  # hide postings older than this; employers often leave stale adverts up for months
DROP_GUARD = 0.5  # a run that finds under half of an employer's previous jobs is treated as a failure, not mass closure


def load(path, default):
    """Missing file: start from the default. A damaged file stops the run, so history is never wiped by accident."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def make_replay_fetch(folder):
    """Serve saved responses: fixtures/<employer-name>.json holds {url_prefix: response}."""
    def for_emp(emp):
        table = load(os.path.join(folder, emp["name"].lower().replace(" ", "-").replace("&", "and") + ".json"), {})

        def fetch(url, data=None):
            for prefix, resp in table.items():
                if url.startswith(prefix):
                    return resp
            raise RuntimeError(f"no saved response for {url[:90]}")
        return fetch
    return for_emp


def clean_city(location, country):
    """First place named in the location, or "" when the posting names only a country or several places."""
    import re
    first = (location or "").split(",")[0].strip()
    low = first.lower()
    if (not first or re.match(r"^\d+\s+locations?$", low) or low.startswith("other cities")
            or (country and country_of(first) == country and not any(
                re.search(r"\b" + re.escape(c) + r"\b", low) for c in CITIES.get(country, [])))):
        return ""
    return first


def normalise(emp, raw, today):
    title = clean_title(raw.get("title", ""))
    disc = discipline_of(title)
    url = (raw.get("url") or "").strip()
    if not disc or not url.startswith("https://"):
        return None
    country = country_of(raw.get("country_hint"), raw.get("location"), raw.get("title")) or ""
    if country in EXCLUDED_COUNTRIES:
        return None
    city = clean_city(raw.get("location"), country)
    return {"id": job_id(emp["name"], raw["id"]), "title": title,
            "emp": emp["name"], "type": emp.get("type", "PMC"), "disc": disc, "level": level_of(title),
            "city": city, "country": country, "region": region_of(country) if country else "Other",
            "url": url, "posted": raw.get("posted") or "", "checked": today, **facts.read(title)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", help="folder of saved responses (offline test run)")
    args = ap.parse_args(argv)
    if args.replay and ROOT == _REAL_ROOT:
        print("A replay run would overwrite the real data/ folder. To check the collector offline run: python -m pytest -q tests")
        return 2

    today = datetime.date.today().isoformat()
    all_emps = load(os.path.join(ROOT, "employers.json"), {}).get("employers", [])
    removed = {e["name"] for e in all_emps if e.get("remove")}  # employer asked to be taken off the board
    employers = [e for e in all_emps if e.get("enabled") and not e.get("remove")]
    state = load(os.path.join(ROOT, "data", "state.json"), {"jobs": {}})
    previous = {j["id"]: j for j in load(os.path.join(ROOT, "data", "jobs.json"), {"jobs": []})["jobs"]}
    fetch_for = make_replay_fetch(args.replay) if args.replay else (lambda emp: get_json)

    jobs, report = {}, []

    def age(j):
        return (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(j.get("checked") or today)).days
    for emp in employers:
        collect = SYSTEMS.get(emp.get("system"))
        if not collect:
            report.append((emp["name"], "skipped", 0, 0, f"unknown system '{emp.get('system')}'"))
            continue
        before = [j for j in previous.values() if j["emp"] == emp["name"]]
        try:
            raw = collect(emp, fetch_for(emp))
            found = {}
            for r in raw:
                j = normalise(emp, r, today)
                if j and j["id"] not in found:
                    found[j["id"]] = j
            if len(before) >= 20 and len(found) < DROP_GUARD * len(before):
                raise RuntimeError(f"found {len(found)} roles, previously {len(before)}; looks like a site or settings problem")
        except Exception as e:
            kept = [j for j in before if age(j) <= KEEP_FAILED_DAYS]
            for j in kept:
                jobs[j["id"]] = j
            hint = " Check tenant/site settings in employers.json." if emp.get("verify") else ""
            report.append((emp["name"], "FAILED", 0, len(kept), f"{type(e).__name__}: {str(e)[:120]}.{hint}"))
            continue
        # read each posting's requirements once; reuse what an earlier run read
        describe = DESCRIBE.get(emp.get("system"))
        described = 0
        raws = {job_id(emp["name"], r["id"]): r for r in raw if r.get("id")}
        for jid, j in found.items():
            old = previous.get(jid) or {}
            if not j.get("posted") and old.get("posted"):
                j["posted"] = old["posted"]  # keep a date read on an earlier run (Workday later shows only "30+ days ago")
            if j.get("posted") and j["posted"] > today:
                j["posted"] = today
            if old.get("fxChecked") and old.get("fxV") == FACTS_VERSION:
                for k in KEEP_KEYS:
                    if old.get(k):
                        j[k] = old[k]
            elif describe and jid in raws and described < MAX_DESCRIBE_PER_RUN:
                described += 1
                try:
                    text = describe(emp, raws[jid], fetch_for(emp))
                    j.update(skills.read_full(text))
                    rq = reqlines.lines(text, limit=9)
                    if rq:
                        j["rq"] = rq
                    fx = facts.read(j["title"], text)
                    for k, v in fx.items():
                        # keep the title's order first, then anything new from the posting text
                        j[k] = list(dict.fromkeys(j.get(k, []) + v)) if k in ("elig", "sector") else v
                    j["skChecked"] = j["fxChecked"] = today
                    j["fx"] = 1
                    j["fxV"] = FACTS_VERSION
                except Exception:
                    # keep what an earlier run read; try again next run
                    for k in KEEP_KEYS[:-2]:
                        if old.get(k):
                            j[k] = old[k]
            else:
                for k in KEEP_KEYS[:-2]:
                    if old.get(k):
                        j[k] = old[k]
        # drop lines every posting of this employer repeats (company blurb), keep the five most telling
        trimmed = reqlines.drop_boilerplate({k: v["rq"] for k, v in found.items() if v.get("rq")})
        for k, ls in trimmed.items():
            if ls:
                found[k]["rq"] = ls[:5]
            else:
                found[k].pop("rq", None)
        jobs.update({k: v for k, v in found.items() if k not in jobs})
        report.append((emp["name"], "ok", len(raw), len(found), ""))

    # employers with no working connector (imported by hand): keep their roles for a while, then let them drop
    collected = {e["name"] for e in employers if SYSTEMS.get(e.get("system"))}
    for name in sorted({j["emp"] for j in previous.values() if not j.get("manual")} - collected - removed):
        kept = [j for j in previous.values() if j["emp"] == name and not j.get("manual") and age(j) <= KEEP_UNCONNECTED_DAYS]
        for j in kept:
            for k, v in facts.read(j.get("title", "")).items():
                j.setdefault(k, v)
            jobs.setdefault(j["id"], j)
        report.append((name, "not connected", 0, len(kept), f"kept from the last import; dropped {KEEP_UNCONNECTED_DAYS} days after it"))

    # jobs added by hand (paid featured posts and one-offs)
    try:
        settings = load(os.path.join(ROOT, "settings.json"), {})
        text, source = manual.read_text(ROOT, settings)
        types = {e["name"]: e.get("type", "PMC") for e in load(os.path.join(ROOT, "employers.json"), {}).get("employers", [])}
        added, problems = manual.parse(text, today, types) if text else ([], [])
        for j in added:
            jobs[j["id"]] = j
        note = f"from {source}; {sum(1 for j in added if j.get('featured'))} featured"
        if problems:
            note += "; problems: " + " | ".join(problems[:10])
        report.append(("Manual jobs", "ok" if not problems else "check", len(added) + len(problems), len(added), note))
    except Exception as e:
        # keep last run's hand-added (often paid) listings rather than dropping them because the sheet was unreachable
        kept = [j for j in previous.values() if j.get("manual") and (j.get("removeAfter") or "9999") >= today]
        for j in kept:
            jobs.setdefault(j["id"], j)
        report.append(("Manual jobs", "FAILED", 0, len(kept), f"{type(e).__name__}: {str(e)[:120]}; kept {len(kept)} from the last run"))

    # first-seen dates; jobs no longer listed simply drop out (closed roles disappear)
    seen = state.get("jobs", {})
    for jid, j in jobs.items():
        j["firstSeen"] = seen.get(jid) or j.get("firstSeen") or today
    state = {"jobs": {jid: j["firstSeen"] for jid, j in jobs.items()}}
    oldest = (datetime.date.fromisoformat(today) - datetime.timedelta(days=MAX_POSTED_DAYS)).isoformat()
    # undated postings: use the day we first saw them instead
    stale = [k for k, j in jobs.items() if not j.get("featured") and (j.get("posted") or j.get("firstSeen") or today) < oldest]
    for k in stale:
        del jobs[k]
    if stale:
        report.append(("All employers", "filtered", 0, len(stale), f"hid postings older than {MAX_POSTED_DAYS} days"))
    ordered = sorted(jobs.values(), key=lambda j: (bool(j.get("featured")), j["firstSeen"], j["posted"]), reverse=True)

    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    payload = {"generated": datetime.datetime.now(datetime.timezone.utc).strftime("%-d %b %Y"), "jobs": ordered}
    with open(os.path.join(ROOT, "data", "jobs.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "data", "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1)
    with open(os.path.join(ROOT, "site", "jobs.js"), "w", encoding="utf-8") as f:
        f.write("window.JOBS_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n")

    lines = [f"# Run report — {payload['generated']}", "", f"**{len(ordered)} project management roles** published.", "",
             "| Employer | Status | Jobs read | Kept | Note |", "|---|---|---|---|---|"]
    lines += [f"| {n} | {s} | {a} | {k} | {note} |" for n, s, a, k, note in report]
    with open(os.path.join(ROOT, "data", "run-report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    for n, s, *_ in report:
        if s == "FAILED":
            print(f"::warning::{n}: could not be read this run (see the run report)")
    ok = [n for n, s, *_ in report if s == "ok" and n != "Manual jobs"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
