"""Builds one real web page per job (site/jobs/<id>.html) and site/sitemap.xml.

Each page has its own address, a proper title and Google's JobPosting data, so the jobs can be
found on Google and shared on LinkedIn or WhatsApp with a preview. The page links to the full
interactive view on the board and to the employer's own posting.

Run after the collector:  python -m collector.pages
"""
import datetime
import html
import sys
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELIG = {"nat": "Nationals only", "citizen": "Citizens / permanent residents only", "clearance": "Security clearance required",
        "nosponsor": "No visa sponsorship", "sponsor": "Visa sponsorship offered", "chartered": "Chartered status or licence asked for"}
BEN = {"housing": "Housing allowance", "transport": "Transport allowance", "flights": "Annual flights home", "medical": "Medical insurance",
       "family": "Family status", "education": "School fees support", "bonus": "Bonus", "pension": "Pension / retirement plan",
       "eosb": "End-of-service gratuity", "leave": "Paid annual leave", "relocation": "Relocation support", "hybrid": "Hybrid / flexible working",
       "rotation": "Rotation schedule", "training": "Training & professional memberships", "life": "Life insurance", "shares": "Employee share plan",
       "inclusive": "Allowances included in the salary package"}
TYPE = {"Developer": "Developer (client)", "PMC": "PMC / consultant", "Contractor": "Contractor"}

CSS = """:root{--bg:#f5f7fa;--surface:#fff;--fg:#0f1b2d;--muted:#566175;--line:#e3e8ef;--accent:#0B5E66;--accent-ink:#0A707A;--green:#067647}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 Inter,system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:820px;margin:0 auto;padding:20px 16px 60px}header a{color:var(--fg);text-decoration:none;font-weight:800;font-size:18px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:24px;margin-top:16px}
h1{font-size:clamp(24px,4vw,32px);line-height:1.15;margin:0 0 6px;letter-spacing:-.02em}.meta{color:var(--muted)}
dl{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 16px;margin:18px 0}dt{font:11px ui-monospace,monospace;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}dd{margin:2px 0 0;font-weight:600}
ul{padding-left:18px}.btn{display:inline-block;padding:12px 18px;border-radius:999px;text-decoration:none;font-weight:700;margin:6px 8px 0 0}
.primary{background:var(--accent);color:#fff}.ghost{border:1px solid var(--line);color:var(--accent-ink)}.fine{font-size:13px;color:var(--muted)}
@media (max-width:560px){dl{grid-template-columns:1fr}}"""


def esc(s):
    return html.escape(str(s or ""), quote=True)


def slug(job_id):
    return re.sub(r"[^a-z0-9-]+", "-", str(job_id).lower()).strip("-")


DEG_LVL = {"B": "Bachelor's degree", "M": "Master's degree", "D": "Diploma or degree"}
DEG_SUBJ = {"construction": "construction management", "civil": "civil engineering", "pm": "project management", "business": "business / finance",
            "qs": "quantity surveying", "engineering": "engineering", "architecture": "architecture", "mechanical": "mechanical engineering",
            "electrical": "electrical engineering"}


def degree_text(d):
    if not d:
        return ""
    lvl, _, sub = d.partition(":")
    subs = [DEG_SUBJ.get(x, x) for x in sub.split(",") if x]
    out = DEG_LVL.get(lvl, "Degree")
    if subs:
        out += " in " + (", ".join(subs[:-1]) + " or " + subs[-1] if len(subs) > 1 else subs[0])
    return out


def iso2(country):
    from .countries import CODES
    for code, name in CODES.items():
        if len(code) == 2 and name == country:
            return code
    return country or ""


def where(j):
    parts = [x for x in (j.get("city"), j.get("country")) if x]
    return ", ".join(dict.fromkeys(parts)) or "Location not stated"


OG = {"Planning": "planning", "Project Controls": "project-controls", "Cost & Commercial": "cost-commercial", "Contracts": "contracts",
      "Claims": "claims", "Risk": "risk", "Project Management": "project-management"}


def page(j, base, today=None):
    today = today or datetime.date.today()
    url = f"{base}/jobs/{slug(j['id'])}.html"
    board = f"{base}/#job/{j['id']}"
    loc = where(j)
    desc = (f"{j['emp']} is hiring a {j['title']} in {loc}. {j.get('disc', '')} role at {j.get('level', '')} level "
            f"with a {TYPE.get(j.get('type'), j.get('type', '')).lower()}. Apply on the employer's own careers site.")
    posted = j.get("posted") or j.get("firstSeen") or ""
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", posted):
        posted = ""
    valid = ""
    if posted:
        try:  # 90 days after posting, but never already in the past while the role is still live
            valid = max(datetime.date.fromisoformat(posted) + datetime.timedelta(days=90), today + datetime.timedelta(days=14)).isoformat()
        except ValueError:
            valid = ""
    ld = {"@context": "https://schema.org/", "@type": "JobPosting", "title": j["title"], "description": f"<p>{esc(desc)}</p>",
          "hiringOrganization": {"@type": "Organization", "name": j["emp"]},
          "jobLocation": {"@type": "Place", "address": {"@type": "PostalAddress", "addressCountry": iso2(j.get("country"))}},
          "employmentType": "FULL_TIME", "directApply": False, "url": url, "identifier": {"@type": "PropertyValue", "name": j["emp"], "value": j["id"]}}
    if j.get("yrs"):
        ld["experienceRequirements"] = {"@type": "OccupationalExperienceRequirements", "monthsOfExperience": int(j["yrs"]) * 12}
    if j.get("deg"):
        ld["educationRequirements"] = {"@type": "EducationalOccupationalCredential",
                                       "credentialCategory": "bachelor degree" if j["deg"][0] == "B" else "postgraduate degree" if j["deg"][0] == "M" else "associate degree"}
    if posted:
        ld["datePosted"] = posted
    if valid:
        ld["validThrough"] = valid + "T23:59:59"
    if j.get("city"):
        ld["jobLocation"]["address"]["addressLocality"] = j["city"]
    pay = j.get("pay") or []
    if len(pay) == 4 and pay[0]:
        lo, hi, cur, per = pay
        hi = hi or lo
        ld["baseSalary"] = {"@type": "MonetaryAmount", "currency": cur or "USD",
                            "value": {"@type": "QuantitativeValue", "minValue": lo, "maxValue": hi, "unitText": (per or "year").upper()}}
    facts = [("Employer", j["emp"]), ("Location", loc), ("Discipline", j.get("disc")), ("Seniority", j.get("level")),
             ("Employer type", TYPE.get(j.get("type"), j.get("type"))), ("Posted", posted or "Not shown by employer"),
             ("Who can apply", " · ".join(ELIG.get(c, c) for c in (j.get("elig") or [])) or "No restriction stated")]
    if j.get("yrs"):
        facts.append(("Experience", f"{j['yrs']}–{j['yrsMax']} years" if j.get("yrsMax") else f"{j['yrs']}+ years"))
    deg = degree_text(j.get("deg"))
    if deg:
        facts.append(("Education", deg))
    req = j.get("rq") or []
    ben = [BEN.get(c, c) for c in (j.get("ben") or []) if c in BEN]
    ld_json = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(j['title'])} at {esc(j['emp'])}, {esc(loc)} | ControlRoles</title>
<meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(url)}">
<meta property="og:title" content="{esc(j['title'])} · {esc(j['emp'])} · {esc(loc)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(url)}"><meta property="og:type" content="website"><meta property="og:site_name" content="ControlRoles"><meta property="og:image" content="{esc(base)}/og/{OG.get(j.get('disc'), 'default')}.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="ControlRoles · {esc(j.get('disc') or 'Project controls')} role"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{esc(base)}/og/{OG.get(j.get('disc'), 'default')}.png">
<script type="application/ld+json">{ld_json}</script><style>{CSS}</style></head>
<body><div class="wrap"><header><a href="{esc(base)}/">Control<span style="color:#0A707A">Roles</span></a> <span class="fine">· project controls jobs</span></header>
<main class="card"><h1>{esc(j['title'])}</h1><div class="meta"><b>{esc(j['emp'])}</b> · {esc(loc)}</div>
<dl>{''.join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in facts)}</dl>
{f'<h2 style="font-size:16px">Requirements (from the posting)</h2><ul>' + ''.join(f'<li>{esc(r)}</li>' for r in req) + '</ul>' if req else ''}
{f'<h2 style="font-size:16px">Benefits listed in the posting</h2><ul>' + ''.join(f'<li>{esc(b)}</li>' for b in ben) + '</ul>' if ben else ''}
<a class="btn primary" href="{esc(j['url'] if str(j.get('url', '')).startswith('https://') else board)}" rel="noopener">Apply on {esc(j['emp'])}'s site ↗</a>
<a class="btn ghost" href="{esc(board)}">Expected salary, benefits &amp; similar roles →</a>
<p class="fine">Listing checked {esc(j.get('checked') or 'recently')}. You apply on the employer's own site; ControlRoles never sees your application.</p></main>
</div></body></html>"""


def main():
    settings = json.load(open(os.path.join(ROOT, "settings.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "settings.json")) else {}
    base = (settings.get("site_url") or "https://controlroles.com").rstrip("/")
    jobs = json.load(open(os.path.join(ROOT, "data", "jobs.json"), encoding="utf-8"))["jobs"]
    out = os.path.join(ROOT, "site", "jobs")
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):  # drop pages of jobs that have closed
        if f.endswith(".html"):
            os.remove(os.path.join(out, f))
    urls = [(f"{base}/", datetime.date.today().isoformat())]
    bad = 0
    for j in jobs:
        try:
            if not (j.get("id") and j.get("title") and j.get("emp")):
                raise ValueError("missing id, title or employer")
            text = page(j, base)
        except Exception as e:  # one odd record must not stop every other page
            bad += 1
            print(f"skipped {j.get('id')}: {e}", file=sys.stderr)
            continue
        name = slug(j["id"]) + ".html"
        with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
            fh.write(text)
        urls.append((f"{base}/jobs/{name}", j.get("checked") or j.get("firstSeen") or datetime.date.today().isoformat()))
    today = datetime.date.today().isoformat()
    with open(os.path.join(ROOT, "site", "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        fh.write("".join(f"<url><loc>{esc(u)}</loc><lastmod>{esc(d)}</lastmod></url>\n" for u, d in urls))
        fh.write("</urlset>\n")
    with open(os.path.join(ROOT, "site", "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
    print(f"{len(urls) - 1} job pages written" + (f", {bad} skipped" if bad else ""))


if __name__ == "__main__":
    main()
