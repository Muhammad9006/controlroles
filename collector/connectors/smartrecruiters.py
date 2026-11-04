"""SmartRecruiters public postings API (e.g. AECOM). Reads every posting, worldwide."""
PAGE = 100
MAX = 5000


def collect(emp, fetch):
    acct, out, offset = emp["account"], [], 0
    while offset < MAX:
        data = fetch(f"https://api.smartrecruiters.com/v1/companies/{acct}/postings?limit={PAGE}&offset={offset}")
        rows = data.get("content") or []
        for p in rows:
            loc = p.get("location") or {}
            out.append({"id": str(p["id"]), "title": p.get("name", ""),
                        "location": ", ".join(x for x in [loc.get("city"), loc.get("region")] if x),
                        "country_hint": (loc.get("country") or "").upper(),
                        "url": f"https://jobs.smartrecruiters.com/{acct}/{p['id']}",
                        "posted": (p.get("releasedDate") or "")[:10]})
        offset += PAGE
        if len(rows) < PAGE or (data.get("totalFound") and offset >= data["totalFound"]):
            break
    return out


def describe(emp, raw, fetch):
    d = fetch(f"https://api.smartrecruiters.com/v1/companies/{emp['account']}/postings/{raw['id']}")
    return " ".join((s or {}).get("text", "") for s in ((d.get("jobAd") or {}).get("sections") or {}).values())
