"""SAP SuccessFactors career sites (e.g. careers.khatibalami.com): the public RSS search feed lists matching jobs with
their full text. One feed per keyword, merged."""
import email.utils
import re
import urllib.parse
import xml.etree.ElementTree as ET

from .. import http

KEYWORDS = ["planning", "planner", "scheduler", "project controls", "cost", "quantity surveyor", "commercial",
            "contracts", "claims", "risk", "project manager", "programme manager", "program manager", "PMO"]

CC = {"SA": "Saudi Arabia", "AE": "United Arab Emirates", "QA": "Qatar", "KW": "Kuwait", "BH": "Bahrain", "OM": "Oman",
      "EG": "Egypt", "JO": "Jordan", "LB": "Lebanon", "IN": "India", "GB": "United Kingdom", "IQ": "Iraq"}


def _get(url, fetch=None):
    return fetch(url) if fetch and fetch is not http.get_json else http.get_text(url)


def collect(emp, fetch=None):
    seen, out = set(), []
    for kw in emp.get("keywords") or KEYWORDS:
        url = f"https://{emp['host']}/services/rss/job/?locale=en_US&keywords=({urllib.parse.quote(kw)})"
        try:
            root = ET.fromstring(_get(url, fetch))
        except ET.ParseError:
            continue
        for it in root.iter("item"):
            link = (it.findtext("link") or "").split("?")[0]
            m = re.search(r"/(\d{6,})/?$", link)
            if not m or m.group(1) in seen:
                continue
            seen.add(m.group(1))
            raw_title = (it.findtext("title") or "").strip()
            loc = re.search(r"\s*\(([^()]*)\)\s*$", raw_title)
            title, city, country = raw_title, "", ""
            if loc and re.search(r"(^|, )[A-Z]{2}$", loc.group(1)):
                title = raw_title[:loc.start()].strip()
                parts = [p.strip() for p in loc.group(1).split(",")]
                country = CC.get(parts[-1], parts[-1])
                city = parts[0] if len(parts) > 1 else ""
            posted = ""
            try:
                posted = email.utils.parsedate_to_datetime(it.findtext("pubDate")).date().isoformat()
            except (TypeError, ValueError):
                pass
            out.append({"id": m.group(1), "title": title, "location": city, "country_hint": country, "url": link,
                        "posted": posted, "text": it.findtext("description") or ""})
    return out


def describe(emp, raw, fetch=None):
    return raw.get("text", "")
