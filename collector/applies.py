"""How many people applied to each job through ControlRoles (clicked Apply to the employer's site), from Google Analytics.

Adds "ap" (people who clicked Apply on that job since it was first listed, up to 90 days) to each job in data/jobs.json
and site/jobs.js, so the site can show "12 applied via ControlRoles". Runs after each collection.
Needs GA_TOKEN (a short-lived read-only Google token from the workflow); without it the counts are left as they were.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROPERTY = os.environ.get("GA_PROPERTY", "562409961")


def counts(token):
    body = {"dateRanges": [{"startDate": "90daysAgo", "endDate": "today"}], "dimensions": [{"name": "pagePath"}],
            "metrics": [{"name": "totalUsers"}], "limit": 10000,
            "dimensionFilter": {"filter": {"fieldName": "eventName", "stringFilter": {"value": "apply_click"}}}}
    req = urllib.request.Request(f"https://analyticsdata.googleapis.com/v1beta/properties/{PROPERTY}:runReport",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read().decode())
    return merge_rows([(row["dimensionValues"][0]["value"], int(float(row["metricValues"][0]["value"]))) for row in out.get("rows", [])])


def merge_rows(rows):
    by_id = {}
    for path, people in rows:
        path = urllib.parse.unquote(path)
        if path.startswith("/job/"):
            jid = path[5:].split("?")[0]
            by_id[jid] = by_id.get(jid, 0) + people
    return by_id


def apply_counts(jobs, by_id):
    for j in jobs:
        n = by_id.get(j["id"], 0)
        if n:
            j["ap"] = n
        else:
            j.pop("ap", None)
    return sum(1 for j in jobs if j.get("ap"))


def main():
    token = os.environ.get("GA_TOKEN")
    if not token:
        print("Apply counts: no Google token this run, counts unchanged.")
        return 0
    path = os.path.join(ROOT, "data", "jobs.json")
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    n = apply_counts(payload["jobs"], counts(token))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "site", "jobs.js"), "w", encoding="utf-8") as f:
        f.write("window.JOBS_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"Apply counts: {n} jobs have people who applied via ControlRoles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
