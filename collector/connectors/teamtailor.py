"""Teamtailor careers sites (e.g. HKA): the public RSS feed at /jobs.rss lists every open job with its text."""
import email.utils
import re
import xml.etree.ElementTree as ET

from .. import http

NS = {"tt": "https://teamtailor.com/locations"}

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")

def _items(emp):
    root = ET.fromstring(_get(f"https://{emp['host']}/jobs.rss"))
    return root.iter("item")

def collect(emp, fetch=None):
    out = []
    for it in _items(emp):
        link = (it.findtext("link") or "").split("?")[0]
        m = re.search(r"/jobs/(\d+)", link)
        if not m:
            continue
        city = country = ""
        for el in it.iter():
            tag = el.tag.split("}")[-1]
            if tag == "city" and not city:
                city = (el.text or "").strip()
            elif tag == "country" and not country:
                country = (el.text or "").strip()
        posted = ""
        if it.findtext("pubDate"):
            try:
                posted = email.utils.parsedate_to_datetime(it.findtext("pubDate")).date().isoformat()
            except (TypeError, ValueError):
                posted = ""
        out.append({"id": m.group(1), "title": (it.findtext("title") or "").strip(), "location": city,
                    "country_hint": country, "url": link, "posted": posted, "text": it.findtext("description") or ""})
    return out

def describe(emp, raw, fetch=None):
    return raw.get("text", "")
