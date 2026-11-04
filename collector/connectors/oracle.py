"""Oracle Recruiting Cloud (Candidate Experience) public API (e.g. WSP).
Searches a set of keywords and pages through results, newest first."""
import urllib.parse

KEYWORDS = ["planner", "planning", "project controls", "scheduler", "cost", "quantity surveyor",
            "contracts", "claims", "commercial", "project manager", "project director"]
PAGE = 25
MAX_PAGES = 80


def collect(emp, fetch):
    host, site = emp["host"], emp["site"]
    seen, out = set(), []
    for kw in KEYWORDS:
        for page in range(MAX_PAGES):
            finder = (f"findReqs;siteNumber={site},limit={PAGE},offset={page * PAGE},"
                      f'keyword="{kw}",sortBy=POSTING_DATES_DESC')
            url = (f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
                   f"?onlyData=true&expand=requisitionList.secondaryLocations&finder={urllib.parse.quote(finder, safe='=;,')}")
            data = fetch(url)
            block = (data.get("items") or [{}])[0]
            items = block.get("requisitionList") or []
            for r in items:
                rid = str(r.get("Id"))
                if rid in seen:
                    continue
                seen.add(rid)
                sec = [s.get("Name", "") for s in (r.get("secondaryLocations") or [])]
                out.append({"id": rid, "title": r.get("Title", ""),
                            "location": ", ".join([r.get("PrimaryLocation") or ""] + sec),
                            "country_hint": r.get("PrimaryLocationCountry") or "",
                            "url": f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{rid}",
                            "posted": (r.get("PostedDate") or "")[:10]})
            total = block.get("TotalJobsCount") or 0
            if len(items) < PAGE or (total and (page + 1) * PAGE >= total):
                break
    return out


def describe(emp, raw, fetch):
    """Full posting text (description, duties, qualifications)."""
    url = (f"https://{emp['host']}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails"
           f'?expand=all&onlyData=true&finder=ById;Id=%22{raw["id"]}%22,siteNumber={emp["site"]}')
    x = (fetch(url).get("items") or [{}])[0]
    return " ".join(x.get(k) or "" for k in ("ExternalDescriptionStr", "ExternalResponsibilitiesStr", "ExternalQualificationsStr"))
