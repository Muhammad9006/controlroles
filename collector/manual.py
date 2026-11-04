"""Jobs added by hand, including paid featured posts.

Where the robot reads them from (first one found wins):
  1. A Google Sheet published as CSV: put its link in settings.json as "manual_jobs_csv_url".
  2. The file manual_jobs.csv in the project folder (edit it on GitHub's website).

Columns (header row required; only title, company and url are compulsory):
  title, company, url, city, country, discipline, seniority, company_type, posted, featured_until, remove_after

- discipline: Planning, Project Controls, Claims, Cost & Commercial, Contracts, Risk or Project Management.
  Left empty, it is worked out from the title (and falls back to Project Management).
- seniority: Mid, Senior, Manager or Director. Left empty, it is worked out from the title.
- company_type: Developer, PMC or Contractor (default PMC, or the type already used for that employer).
- posted: YYYY-MM-DD (default: the day the robot first sees the row).
- featured_until: YYYY-MM-DD. Until this date the job is pinned to the top with a "Featured" badge.
- remove_after: YYYY-MM-DD. After this date the job disappears. Otherwise the normal 90-day rule applies.
- Rows whose title starts with # are ignored, so you can keep notes or switch a job off.
"""
import csv
import io
import os
import re
import urllib.request

from .classify import clean_title, country_of, discipline_of, level_of
from .facts import read as read_facts
from .countries import COUNTRIES, EXCLUDED_COUNTRIES, region_of
from .http import UA
from .ids import job_id

DISCIPLINES = ["Planning", "Project Controls", "Claims", "Cost & Commercial", "Contracts", "Risk", "Project Management"]
LEVELS = ["Mid", "Senior", "Manager", "Director"]
TYPES = ["Developer", "PMC", "Contractor"]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# friendly column names (e.g. Google Form questions) -> the names used below
ALIASES = {"job title": "title", "role": "title", "company name": "company", "employer": "company",
           "job link": "url", "link": "url", "link to the job": "url", "apply link": "url",
           "company type": "company_type", "posting date": "posted", "date posted": "posted",
           "featured until": "featured_until", "feature until": "featured_until",
           "remove after": "remove_after", "remove on": "remove_after", "show": "approved", "approve": "approved"}


def _date(v):
    """Accept YYYY-MM-DD, plus the D/M/YYYY and M/D/YYYY that Google Forms and Sheets produce."""
    v = (v or "").strip().split(" ")[0]
    if not v or DATE.match(v):
        return v
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", v)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), m.group(3)
        d, mo = (a, b) if a > 12 else (b, a) if b > 12 else (a, b)  # ambiguous dates are read day/month
        return f"{y}-{mo:02d}-{d:02d}"
    return v


def _pick(value, options):
    v = (value or "").strip().lower()
    return next((o for o in options if o.lower() == v), "")


def read_text(root, settings, fetch_text=None):
    """Return (csv_text, source_label) or ("", reason)."""
    url = (settings.get("manual_jobs_csv_url") or "").strip()
    if url:
        if fetch_text:
            return fetch_text(url), "Google Sheet"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8-sig"), "Google Sheet"
    path = os.path.join(root, "manual_jobs.csv")
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            return f.read(), "manual_jobs.csv"
    return "", "no manual jobs file"


def parse(text, today, types=None):
    """Turn CSV text into job records. Returns (jobs, problems)."""
    types = types or {}
    jobs, problems = [], []
    rows = csv.DictReader(io.StringIO(text))
    for n, row in enumerate(rows, start=2):  # row 1 is the header
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        row = {ALIASES.get(k, k): v for k, v in row.items()}
        for k in ("posted", "featured_until", "remove_after"):
            row[k] = _date(row.get(k))
        if "approved" in row and row["approved"].strip().lower() not in ("yes", "y", "true", "1", "approved", "✓"):
            continue
        title, company, url = clean_title(row.get("title", "")), row.get("company", ""), row.get("url", "")
        if not (title or company or url) or title.startswith("#"):
            continue
        if not (title and company and url):
            problems.append(f"row {n}: title, company and url are all needed")
            continue
        if not url.startswith("https://"):
            problems.append(f"row {n}: the link must start with https://")
            continue
        bad_dates = [k for k in ("posted", "featured_until", "remove_after") if row.get(k) and not DATE.match(row[k])]
        if bad_dates:
            problems.append(f"row {n}: write {', '.join(bad_dates)} as YYYY-MM-DD")
            continue
        if row.get("remove_after") and row["remove_after"] < today:
            continue
        country = row.get("country", "")
        country = country if country in COUNTRIES else (country_of(country, row.get("city"), title) or country)
        if country in EXCLUDED_COUNTRIES:
            problems.append(f"row {n}: {country} is excluded from the board")
            continue
        disc = _pick(row.get("discipline"), DISCIPLINES) or discipline_of(title) or "Project Management"
        level = _pick(row.get("seniority"), LEVELS) or level_of(title)
        ctype = _pick(row.get("company_type"), TYPES) or types.get(company) or "PMC"
        featured_until = row.get("featured_until", "")
        job = {"id": job_id(company, "manual-" + re.sub(r"[^a-z0-9]+", "-", url.lower())[-60:]),
               "title": title, "emp": company, "type": ctype, "disc": disc, "level": level,
               "city": row.get("city", ""), "country": country,
               "region": region_of(country) if country in COUNTRIES else "Other",
               "url": url, "posted": row.get("posted", ""), "checked": today, "manual": True, **read_facts(title)}
        if featured_until and featured_until >= today:
            job["featured"] = True
            job["featuredUntil"] = featured_until
        if row.get("remove_after"):
            job["removeAfter"] = row["remove_after"]
        jobs.append(job)
    return jobs, problems
