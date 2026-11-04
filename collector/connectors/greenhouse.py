"""Greenhouse public job board API."""


def collect(emp, fetch):
    data = fetch(f"https://boards-api.greenhouse.io/v1/boards/{emp['account']}/jobs")
    return [{"id": str(j["id"]), "title": j.get("title", ""), "location": (j.get("location") or {}).get("name", ""),
             "country_hint": "", "url": j.get("absolute_url", ""), "posted": (j.get("updated_at") or "")[:10]}
            for j in data.get("jobs") or []]
