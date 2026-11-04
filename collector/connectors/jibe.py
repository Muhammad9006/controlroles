"""Jibe / iCIMS career sites (e.g. KEO at careers.keo.com). Public JSON at /api/jobs, 100 per page, with descriptions."""
PAGE = 100


def collect(emp, fetch):
    host, out = emp["host"], []
    for page in range(1, 51):
        data = fetch(f"https://{host}/api/jobs?page={page}&limit={PAGE}")
        rows = [j.get("data") or {} for j in data.get("jobs") or []]
        for j in rows:
            out.append({"id": str(j.get("req_id") or j.get("slug")), "title": j.get("title", ""),
                        "location": ", ".join(x for x in [j.get("city"), j.get("state")] if x),
                        "country_hint": (j.get("country_code") or "").upper(),
                        "url": f"https://{host}/jobs/{j.get('slug') or j.get('req_id')}",
                        "posted": (j.get("posted_date") or j.get("create_date") or "")[:10],
                        "_text": " ".join(j.get(k) or "" for k in ("description", "qualifications", "responsibilities"))})
        if len(rows) < PAGE:
            break
    return out


def describe(emp, raw, fetch):
    return raw.get("_text", "")
