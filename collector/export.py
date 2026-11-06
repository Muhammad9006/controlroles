"""One-off analytics export for a performance review: Google Analytics (last 7 days and by day) plus board numbers.
The workflow encrypts the result with a public key given at run time, so the public run log only shows ciphertext."""
import json
import os
import sys
import urllib.parse
import urllib.request

from collector import brief, alerts


def q(token, dims, mets, start="7daysAgo", end="yesterday", limit=50, flt=None, order=None):
    body = {"dateRanges": [{"startDate": start, "endDate": end}], "dimensions": [{"name": d} for d in dims],
            "metrics": [{"name": m} for m in mets], "limit": limit}
    if flt:
        body["dimensionFilter"] = flt
    body["orderBys"] = [{"metric": {"metricName": order or mets[0]}, "desc": True}] if not dims or dims[0] != "date" else [{"dimension": {"dimensionName": "date"}}]
    return {"dims": dims, "mets": mets, "rows": brief.ga(token, body)}


def main():
    t = os.environ["GA_TOKEN"]
    ev = lambda name: {"filter": {"fieldName": "eventName", "stringFilter": {"value": name}}}
    out = {
        "daily": q(t, ["date"], ["activeUsers", "newUsers", "sessions", "screenPageViews", "engagementRate", "averageSessionDuration", "bounceRate"], start="14daysAgo", end="today"),
        "channels": q(t, ["sessionDefaultChannelGroup"], ["activeUsers", "sessions", "engagementRate"]),
        "sources": q(t, ["sessionSource", "sessionMedium"], ["activeUsers", "sessions", "engagementRate"], limit=30),
        "countries": q(t, ["country"], ["activeUsers", "sessions", "engagementRate"], limit=30),
        "cities": q(t, ["city", "country"], ["activeUsers"], limit=30),
        "devices": q(t, ["deviceCategory"], ["activeUsers", "engagementRate"]),
        "newret": q(t, ["newVsReturning"], ["activeUsers", "sessions"]),
        "landing": q(t, ["landingPage"], ["sessions", "activeUsers"], limit=30),
        "pages": q(t, ["pagePath"], ["screenPageViews", "activeUsers"], limit=60),
        "events": q(t, ["eventName"], ["eventCount", "totalUsers"], limit=40),
        "apply_by_page": q(t, ["pagePath"], ["eventCount", "totalUsers"], flt=ev("apply_click"), limit=60),
        "apply_by_source": q(t, ["sessionSource"], ["eventCount", "totalUsers"], flt=ev("apply_click"), limit=20),
        "apply_by_country": q(t, ["country"], ["eventCount", "totalUsers"], flt=ev("apply_click"), limit=20),
        "share": q(t, ["pagePath"], ["eventCount"], flt=ev("share"), limit=20),
        "hours": q(t, ["hour"], ["activeUsers"], limit=24),
    }
    with open("data/jobs.json", encoding="utf-8") as f:
        jobs = json.load(f)["jobs"]
    out["job_titles"] = {"/job/" + j["id"]: f"{j['title']} · {j['emp']} · {j.get('country','')} · {j.get('disc','')}" for j in jobs}
    import collections
    out["board"] = {"total": len(jobs), "by_region": collections.Counter(j.get("region") for j in jobs).most_common(),
                    "by_disc": collections.Counter(j.get("disc") for j in jobs).most_common(),
                    "by_emp": collections.Counter(j.get("emp") for j in jobs).most_common(40),
                    "by_firstseen": sorted(collections.Counter(j.get("firstSeen") for j in jobs).items()),
                    "with_salary": sum(1 for j in jobs if j.get("sal") or j.get("salary"))}
    cf = os.environ.get("CLOUDFLARE_API_TOKEN")
    if cf:
        acc, ns = alerts.kv_ids(cf)
        subs = alerts.load_subs(cf, acc, ns)
        out["subscribers"] = {"total": len(subs), "confirmed": sum(1 for s in subs if s.get("status") == "confirmed"),
                              "freq": collections.Counter((s.get("prefs") or {}).get("freq") for s in subs).most_common(),
                              "disc": collections.Counter(d for s in subs for d in ((s.get("prefs") or {}).get("disc") or ["(all)"])).most_common(),
                              "region": collections.Counter((s.get("prefs") or {}).get("region") or "(any)" for s in subs).most_common(),
                              "created": sorted(collections.Counter((s.get("created") or "")[:10] for s in subs).items())}
        try:
            raw = alerts._req(f"{alerts.CF}/accounts/{acc}/storage/kv/namespaces/{ns}/values/applycounts", cf, raw=True)
            c = json.loads(raw)
            out["live_applies"] = {"jobs": len(c), "people": sum(c.values()), "top": sorted(c.items(), key=lambda x: -x[1])[:30]}
        except Exception as e:
            out["live_applies"] = str(e)
    json.dump(out, open("export.json", "w"))
    print("export ready", os.path.getsize("export.json"))


if __name__ == "__main__":
    sys.exit(main())
