"""Morning brief: yesterday's visitors and where they came from (Google Analytics), plus the board's own numbers,
emailed to the owner every morning.

Run by .github/workflows/daily-brief.yml, which signs in to Google without any stored key (Workload Identity) and
passes a short-lived read-only token in GA_TOKEN. Needs RESEND_API_KEY to send; BRIEF_TO sets the recipient.
  python -m collector.brief            send the email
  python -m collector.brief --print    print it instead (no email)
"""
import datetime as dt
import html
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROPERTY = os.environ.get("GA_PROPERTY", "562409961")
TO = os.environ.get("BRIEF_TO", "hello@controlroles.com")
SITE = "https://controlroles.com"


# ---------- Google Analytics ----------

def ga(token, body):
    req = urllib.request.Request(f"https://analyticsdata.googleapis.com/v1beta/properties/{PROPERTY}:runReport",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read().decode())
    rows = []
    for row in out.get("rows", []):
        rows.append([d["value"] for d in row.get("dimensionValues", [])] + [float(m["value"]) for m in row.get("metricValues", [])])
    return rows


def fetch(token):
    days = lambda a, b: [{"startDate": a, "endDate": b}]
    m = lambda *n: [{"name": x} for x in n]
    d = lambda *n: [{"name": x} for x in n]
    data = {}
    data["totals"] = ga(token, {"dateRanges": days("yesterday", "yesterday") + days("2daysAgo", "2daysAgo"),
                                "metrics": m("activeUsers", "newUsers", "sessions", "screenPageViews", "engagementRate", "averageSessionDuration")})
    data["week"] = ga(token, {"dateRanges": days("7daysAgo", "yesterday"), "dimensions": d("date"), "metrics": m("activeUsers"),
                              "orderBys": [{"dimension": {"dimensionName": "date"}}]})
    data["channels"] = ga(token, {"dateRanges": days("yesterday", "yesterday"), "dimensions": d("sessionDefaultChannelGroup"),
                                  "metrics": m("activeUsers", "sessions"), "orderBys": [{"metric": {"metricName": "activeUsers"}, "desc": True}], "limit": 8})
    data["sources"] = ga(token, {"dateRanges": days("yesterday", "yesterday"), "dimensions": d("sessionSource", "sessionMedium"),
                                 "metrics": m("activeUsers"), "orderBys": [{"metric": {"metricName": "activeUsers"}, "desc": True}], "limit": 8})
    data["countries"] = ga(token, {"dateRanges": days("yesterday", "yesterday"), "dimensions": d("country"),
                                   "metrics": m("activeUsers"), "orderBys": [{"metric": {"metricName": "activeUsers"}, "desc": True}], "limit": 8})
    data["devices"] = ga(token, {"dateRanges": days("yesterday", "yesterday"), "dimensions": d("deviceCategory"), "metrics": m("activeUsers")})
    data["pages"] = ga(token, {"dateRanges": days("yesterday", "yesterday"), "dimensions": d("pagePath"),
                               "metrics": m("screenPageViews"), "orderBys": [{"metric": {"metricName": "screenPageViews"}, "desc": True}], "limit": 25})
    data["events"] = ga(token, {"dateRanges": days("yesterday", "yesterday"), "dimensions": d("eventName"), "metrics": m("eventCount"),
                                "dimensionFilter": {"filter": {"fieldName": "eventName", "inListFilter": {"values": ["apply_click", "share", "alert_signup"]}}}})
    return data


# ---------- the brief (pure, tested offline) ----------

def pct(a, b):
    if not b:
        return None
    return round((a - b) / b * 100)


def change(a, b):
    p = pct(a, b)
    if p is None:
        return "new" if a else "—"
    return f"{'+' if p > 0 else ''}{p}% vs day before"


def build(data, jobs, day):
    """Returns (subject, html, text)."""
    tot = {r[0]: r[1:] for r in data.get("totals", [])} if data.get("totals") and isinstance(data["totals"][0][0], str) else {}
    # with two date ranges GA adds a dateRange dimension: date_range_0 = yesterday, date_range_1 = day before
    y = tot.get("date_range_0", [0] * 6)
    p = tot.get("date_range_1", [0] * 6)
    users, new_users, sessions, views, engage, dur = y
    titles = {"/job/" + j["id"]: f"{j['title']} · {j['emp']}" for j in jobs}
    ev = {r[0]: int(r[1]) for r in data.get("events", [])}
    jobs_views = [(titles.get(urllib.parse.unquote(path), path), int(v)) for path, v in data.get("pages", []) if path.startswith("/job/")][:8]
    new_jobs = sum(1 for j in jobs if j.get("firstSeen") == day)
    channels = [(c, int(u)) for c, u, _s in data.get("channels", [])]
    sources = [(f"{s} / {m}", int(u)) for s, m, u in data.get("sources", [])]
    countries = [(c, int(u)) for c, u in data.get("countries", [])]
    devices = {dname: int(u) for dname, u in data.get("devices", [])}
    week = [(r[0], int(r[1])) for r in data.get("week", [])]

    hi = []
    if users:
        hi.append(f"{int(users)} visitors ({change(users, p[0])}), {int(new_users)} of them new.")
    else:
        hi.append("No visitors were recorded yesterday.")
    if channels and users:
        c, u = channels[0]
        hi.append(f"Most visitors came from {c} ({round(u / users * 100)}%).")
    if countries and users:
        hi.append(f"Top country: {countries[0][0]} ({countries[0][1]} visitors).")
    if jobs_views:
        hi.append(f"Most-viewed job: {jobs_views[0][0]} ({jobs_views[0][1]} views).")
    if ev.get("apply_click"):
        hi.append(f"{ev['apply_click']} Apply clicks sent visitors to employers' sites.")
    if devices and users:
        mob = devices.get("mobile", 0)
        hi.append(f"{round(mob / users * 100)}% of visitors were on a phone.")
    week_total = sum(u for _, u in week)
    if len(week) >= 2:
        hi.append(f"Last 7 days: {week_total} visitors in total.")

    subject = f"ControlRoles brief · {day}: {int(users)} visitors" + (f" ({change(users, p[0]).split(' ')[0]})" if p[0] else "")
    e = html.escape

    def table(title, rows, col="Visitors"):
        if not rows:
            return ""
        body = "".join(f'<tr><td style="padding:6px 0;border-top:1px solid #E3EAEC">{e(str(a))}</td>'
                       f'<td style="padding:6px 0;border-top:1px solid #E3EAEC;text-align:right;font-weight:700">{b}</td></tr>' for a, b in rows)
        return (f'<h3 style="font-size:15px;margin:22px 0 6px">{e(title)}</h3><table width="100%" cellpadding="0" cellspacing="0" '
                f'style="font-size:14px"><tr><td style="color:#6B7F84;font-size:12px">&nbsp;</td><td style="color:#6B7F84;font-size:12px;text-align:right">{col}</td></tr>{body}</table>')

    def tile(label, value, sub=""):
        return (f'<td style="padding:12px;background:#F1F4F6;border-radius:10px;width:25%"><div style="color:#6B7F84;font-size:12px">{e(label)}</div>'
                f'<div style="font-size:22px;font-weight:800">{value}</div><div style="color:#6B7F84;font-size:11px">{e(sub)}</div></td>')

    tiles = ("<table width='100%' cellpadding='0' cellspacing='6'><tr>" +
             tile("Visitors", int(users), change(users, p[0])) + tile("Page views", int(views), change(views, p[3])) +
             tile("Engaged", f"{round(engage * 100)}%", f"avg {round(dur)}s per visit") +
             tile("New jobs", new_jobs, f"{len(jobs):,} live") + "</tr></table>")
    actions = [("Apply clicks", ev.get("apply_click", 0)), ("Shares", ev.get("share", 0)), ("Alert sign-ups", ev.get("alert_signup", 0))]
    html_body = f"""<div style="font:15px/1.55 Arial,Helvetica,sans-serif;color:#0B1D22;max-width:640px;margin:0 auto">
<p style="font-size:20px;font-weight:800;margin:0">Control<span style="color:#0A707A">Roles</span> · morning brief</p>
<p style="color:#3D5359;margin:2px 0 14px">Yesterday, {e(day)} (Riyadh time)</p>
{tiles}
<h3 style="font-size:15px;margin:22px 0 6px">What stood out</h3><ul style="margin:0;padding-left:18px">{''.join(f'<li>{e(h)}</li>' for h in hi)}</ul>
{table("Where visitors came from", channels)}
{table("Top sources", sources)}
{table("Countries", countries)}
{table("Devices", sorted(devices.items(), key=lambda x: -x[1]))}
{table("Most-viewed jobs", jobs_views, "Views")}
{table("Actions", actions, "Count")}
{table("Visitors per day (last 7 days)", [(dt.datetime.strptime(dd, "%Y%m%d").strftime("%a %d %b"), u) for dd, u in week])}
<p style="color:#6B7F84;font-size:12px;border-top:1px solid #CFDCDF;padding-top:10px;margin-top:22px">
From Google Analytics (visitors who accepted analytics cookies; European visitors who decline aren't counted).
<a href="https://analytics.google.com/" style="color:#6B7F84">Open Google Analytics</a> · <a href="{SITE}" style="color:#6B7F84">controlroles.com</a></p></div>"""
    text = "\n".join([f"ControlRoles morning brief, {day}", ""] + [f"- {h}" for h in hi] + ["", "Channels:"] +
                     [f"  {a}: {b}" for a, b in channels] + ["Countries:"] + [f"  {a}: {b}" for a, b in countries] +
                     ["Most-viewed jobs:"] + [f"  {a}: {b}" for a, b in jobs_views])
    return subject, html_body, text


def main(argv):
    token, key = os.environ.get("GA_TOKEN"), os.environ.get("RESEND_API_KEY")
    if not token:
        print("Morning brief: no Google Analytics access token (run it from the daily-brief workflow).")
        return 0
    day = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3) - dt.timedelta(days=1)).date().isoformat()
    with open(os.path.join(ROOT, "data", "jobs.json"), encoding="utf-8") as f:
        jobs = json.load(f)["jobs"]
    subject, body, text = build(fetch(token), jobs, day)
    if "--print" in argv or not key:
        print(subject)
        print(text)
        return 0
    req = urllib.request.Request("https://api.resend.com/emails", method="POST",
                                 data=json.dumps({"from": "ControlRoles <alerts@controlroles.com>", "to": [TO], "subject": subject,
                                                  "html": body, "text": text}).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "ControlRolesBot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        r.read()
    print(f"Morning brief sent to {TO}: {subject}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
