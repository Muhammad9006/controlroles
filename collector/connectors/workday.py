"""Workday career sites (e.g. Parsons). Uses the same search the public careers page uses."""
import datetime
import re

KEYWORDS = ["planner", "planning", "project controls", "scheduler", "cost", "quantity surveyor",
            "contracts", "claims", "commercial", "project manager", "project director"]
PAGE = 20
MAX_PAGES = 100  # Workday stops at 2,000 results per search


def _posted(text):
    """Workday gives 'Posted Today', 'Posted 3 Days Ago', 'Posted 30+ Days Ago'."""
    if not text:
        return ""
    today = datetime.date.today()
    t = text.lower()
    if "today" in t:
        return today.isoformat()
    if "yesterday" in t:
        return (today - datetime.timedelta(days=1)).isoformat()
    if "+" in t:  # "30+ Days Ago": the real date is unknown, and counting it as 30 days would never let it expire
        return ""
    m = re.search(r"(\d+)", t)
    return (today - datetime.timedelta(days=int(m.group(1)))).isoformat() if m else ""


def collect(emp, fetch):
    tenant, wd, site = emp["tenant"], emp["wd"], emp["site"]
    base = f"https://{tenant}.{wd}.myworkdayjobs.com"
    api = f"{base}/wday/cxs/{tenant}/{site}/jobs"
    seen, out = set(), []
    for kw in KEYWORDS:
        for page in range(MAX_PAGES):
            data = fetch(api, {"appliedFacets": {}, "limit": PAGE, "offset": page * PAGE, "searchText": kw})
            rows = data.get("jobPostings") or []
            for p in rows:
                path = p.get("externalPath") or ""
                if not path or path in seen:
                    continue
                seen.add(path)
                out.append({"id": path.rsplit("_", 1)[-1], "title": p.get("title", ""),
                            "location": p.get("locationsText") or "", "country_hint": "",
                            "url": f"{base}/en-US/{site}{path}", "posted": _posted(p.get("postedOn"))})
            total = data.get("total") or 0
            if len(rows) < PAGE or (total and (page + 1) * PAGE >= total):
                break
    return out


def describe(emp, raw, fetch):
    base = f"https://{emp['tenant']}.{emp['wd']}.myworkdayjobs.com"
    path = raw["url"].split(f"/{emp['site']}", 1)[1]
    d = fetch(f"{base}/wday/cxs/{emp['tenant']}/{emp['site']}{path}")
    return (d.get("jobPostingInfo") or {}).get("jobDescription") or ""
