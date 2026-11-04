"""Teamtailor careers sites (e.g. HKA): the public RSS feed at /jobs.rss lists every open job with its text."""
import email.utils
import re
import xml.etree.ElementTree as ET

from .. import http

NS = {"tt": "https://teamtailor.com/locations"}

def _get(url, fetch=None):
    return fetch(url) if fetch and fetch is not http.get_json else http.get_text(url)  # live runs pass the JSON helper; RSS needs plain text


def _items(emp, fetch=None):
    root = ET.fromstring(_get(f"https://{emp['host']}/jobs.rss", fetch))
    return root.iter("item")

def collect(emp, fetch=None):
    out = []
    for it in _items(emp, fetch):
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
