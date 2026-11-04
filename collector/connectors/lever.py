"""Lever public postings API (e.g. Aldar)."""
import datetime


def collect(emp, fetch):
    data = fetch(f"https://api.lever.co/v0/postings/{emp['account']}?mode=json")
    out = []
    for p in data:
        cats = p.get("categories") or {}
        locs = [cats.get("location") or ""] + list(cats.get("allLocations") or [])
        posted = ""
        if p.get("createdAt"):
            posted = datetime.datetime.fromtimestamp(p["createdAt"] / 1000, datetime.timezone.utc).date().isoformat()
        out.append({"id": p["id"], "title": p.get("text", ""), "location": ", ".join(l for l in locs if l),
                    "country_hint": p.get("country") or "", "url": p.get("hostedUrl", ""), "posted": posted})
    return out


def describe(emp, raw, fetch):
    d = fetch(f"https://api.lever.co/v0/postings/{emp['account']}/{raw['id']}")
    lists = " ".join(f"{l.get('text', '')} {l.get('content', '')}" for l in d.get("lists") or [])
    return " ".join([d.get("descriptionPlain") or "", d.get("additionalPlain") or "", lists])
