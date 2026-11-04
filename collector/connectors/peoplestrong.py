"""PeopleStrong candidate portals (e.g. Larsen & Toubro, Sobha): POST /api/cp/rest/altone/cp/jobs/v1.

The list already carries the posted date, the experience range ("5-10 years") and the skills, so no second
call per job is needed for those; `describe` returns what the list gave us.
"""


def _rows(emp, fetch):
    host = emp["host"]
    out, offset, total = [], 0, None
    while total is None or offset < total:
        data = fetch(f"https://{host}/api/cp/rest/altone/cp/jobs/v1?offset={offset}&limit=99", data={})
        rows = data.get("response") or []
        total = data.get("totalRecords") or 0
        out.extend(rows)
        if len(rows) < 99 or offset > 6000:
            break
        offset += 99
    return out


def _title(t):
    import re
    t = re.sub(r"\s*/\s*\d+\s*/\s*\w+\s*$", "", t or "")      # "Scheduling Engineer /1029/2B"
    t = re.sub(r"^[A-Z]{2,5}_[A-Z]{2,4}_", "", t).replace("_", " ")  # "RCF_IC_Contract_Administration"
    return {"Planning": "Planning Engineer", "Billing": "Billing Engineer"}.get(t.strip(), t.strip())


def collect(emp, fetch):
    out = []
    for r in _rows(emp, fetch):
        parts = [p.strip() for p in (r.get("locationHierarchyComplete") or "").split(">") if p.strip()]
        code = (r.get("jobCode") or "").replace("/", "_")
        url = (r.get("jobDetailUrl") or "").split("?")[0] or f"https://{emp['host']}/job/detail/{code}"
        out.append({"id": code, "title": _title(r.get("jobTitle")), "location": parts[-1] if len(parts) > 1 else "",
                    "country_hint": parts[0] if parts else "", "url": url, "posted": r.get("jobPostedDate") or "",
                    "exp": r.get("expRange") or ""})
    return out


def describe(emp, raw, fetch):
    # the portal's detail call needs a session; the list's experience range is enough to read the years
    return f"Experience: {raw.get('exp', '')}" if raw.get("exp") else ""
