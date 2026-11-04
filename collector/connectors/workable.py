"""Workable public job widget (common with GCC contractors and smaller firms)."""


def collect(emp, fetch):
    data = fetch(f"https://apply.workable.com/api/v1/widget/accounts/{emp['account']}")
    out = []
    for j in data.get("jobs") or []:
        out.append({"id": j.get("shortcode", ""), "title": j.get("title", ""),
                    "location": ", ".join(x for x in [j.get("city"), j.get("state")] if x),
                    "country_hint": j.get("country") or "",
                    "url": j.get("url") or f"https://apply.workable.com/{emp['account']}/j/{j.get('shortcode')}/",
                    "posted": (j.get("published_on") or "")[:10]})
    return out


def describe(emp, raw, fetch):
    d = fetch(f"https://apply.workable.com/api/v2/accounts/{emp['account']}/jobs/{raw['id']}")
    return " ".join(d.get(k) or "" for k in ("description", "requirements", "benefits"))
