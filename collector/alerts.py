"""Send the job-alert emails.

Subscribers sign up on the site; the sign-up service (worker/alerts.js) keeps them in Cloudflare KV.
After each collection run this script reads the confirmed subscribers, picks the roles that appeared since
their last email and match their alert, and sends them through Resend.
  daily  subscribers: at most one email a day
  weekly subscribers: at most one email every 7 days
Nothing is sent when there are no new matching roles (the subscriber's clock still moves on).

Needs the GitHub secrets CLOUDFLARE_API_TOKEN and RESEND_API_KEY. Without them it does nothing.
Run: python -m collector.alerts            (send)
     python -m collector.alerts --dry-run  (show what would be sent, send nothing)
"""
import datetime as dt
import html
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://controlroles.com"
API = "https://api.controlroles.com"
FROM = "ControlRoles <alerts@controlroles.com>"
REPLY_TO = "hello@controlroles.com"
KV_TITLE = "controlroles-subs"
DAILY_CAP = int(os.environ.get("ALERT_DAILY_CAP", "60"))   # the free Resend plan sends 100 a day; leave room for confirmations
PER_EMAIL = 12
CF = "https://api.cloudflare.com/client/v4"


# ---------- matching (pure, tested offline) ----------

def matches(job, prefs):
    disc = prefs.get("disc") or []
    return ((not disc or job.get("disc") in disc)
            and (not prefs.get("region") or job.get("region") == prefs["region"])
            and (not prefs.get("country") or job.get("country") == prefs["country"])
            and (not prefs.get("level") or job.get("level") == prefs["level"]))


def due(sub, today):
    """Is this subscriber due an email today?"""
    last = sub.get("last") or "2000-01-01"
    gap = 1 if (sub.get("prefs") or {}).get("freq") == "daily" else 7
    return (dt.date.fromisoformat(today) - dt.date.fromisoformat(last)).days >= gap


def new_for(sub, jobs):
    last = sub.get("last") or "2000-01-01"
    hits = [j for j in jobs if (j.get("firstSeen") or "") > last and matches(j, sub.get("prefs") or {})]
    hits.sort(key=lambda j: (j.get("firstSeen") or "", j.get("posted") or ""), reverse=True)
    return hits


def describe(p):
    disc = ", ".join(p.get("disc") or []) or "All disciplines"
    return " · ".join([disc, p.get("country") or p.get("region") or "Worldwide", p.get("level") or "All levels"])


def list_link(p):
    q = {k: p[k] for k in ("region", "country", "level") if p.get(k)}
    if len(p.get("disc") or []) == 1:
        q["disc"] = p["disc"][0]
    q["sort"] = "new"
    return f"{SITE}/#jobs?{urllib.parse.urlencode(q, quote_via=urllib.parse.quote)}"


def build_email(sub, hits):
    p = sub.get("prefs") or {}
    e = html.escape
    n = len(hits)
    shown = hits[:PER_EMAIL]
    unsub = f"{API}/unsubscribe?e={urllib.parse.quote(sub['email'])}&t={sub['token']}"
    what = (p.get("disc") or ["project controls"])
    what = what[0] if len(what) == 1 else "matching"
    subject = f"{n} new {what} role{'s' if n != 1 else ''}" + (f" in {p.get('country') or p.get('region')}" if (p.get("country") or p.get("region")) else "")
    rows = []
    for j in shown:
        place = ", ".join(x for x in (j.get("city"), j.get("country")) if x)
        link = f"{SITE}/#job/{urllib.parse.quote(j['id'], safe='')}"
        rows.append(f"""<tr><td style="padding:12px 0;border-top:1px solid #CFDCDF">
<a href="{e(link)}" style="color:#0A707A;font-weight:700;font-size:16px;text-decoration:none">{e(j.get('title', ''))}</a><br>
<span style="color:#3D5359;font-size:14px">{e(j.get('emp', ''))} · {e(place)}{' · ' + e(j['level']) if j.get('level') else ''}</span></td></tr>""")
    more = (f'<p><a href="{e(list_link(p))}" style="color:#0A707A;font-weight:700">See all {n} new roles on ControlRoles →</a></p>'
            if n > len(shown) else f'<p><a href="{e(list_link(p))}" style="color:#0A707A;font-weight:700">Browse all matching roles →</a></p>')
    body = f"""<div style="font:15px/1.55 Arial,Helvetica,sans-serif;color:#0B1D22;max-width:600px;margin:0 auto">
<p style="font-size:20px;font-weight:800;margin:0 0 4px">Control<span style="color:#0A707A">Roles</span></p>
<p style="color:#3D5359;margin:0 0 16px">New roles for your alert: <b>{e(describe(p))}</b></p>
<table role="presentation" cellpadding="0" cellspacing="0" width="100%">{''.join(rows)}</table>
{more}
<p style="color:#6B7F84;font-size:12px;border-top:1px solid #CFDCDF;padding-top:12px;margin-top:20px">
You get this {'daily' if p.get('freq') == 'daily' else 'weekly'} email because you set up a job alert on controlroles.com.
<a href="{SITE}/#alerts" style="color:#6B7F84">Change your alert</a> · <a href="{e(unsub)}" style="color:#6B7F84">Unsubscribe</a></p></div>"""
    lines = [f"New roles for your alert: {describe(p)}", ""]
    for j in shown:
        lines += [j.get("title", ""), f"{j.get('emp', '')} · {', '.join(x for x in (j.get('city'), j.get('country')) if x)}",
                  f"{SITE}/#job/{urllib.parse.quote(j['id'], safe='')}", ""]
    lines += [f"See all: {list_link(p)}", "", f"Unsubscribe: {unsub}"]
    return {"from": FROM, "reply_to": REPLY_TO, "to": [sub["email"]], "subject": subject, "html": body, "text": "\n".join(lines),
            "headers": {"List-Unsubscribe": f"<{unsub}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}}


def plan(subs, jobs, today, cap):
    """Decide who gets what. Returns (emails, updates, deferred)."""
    emails, updates, deferred = [], {}, 0
    confirmed = [s for s in subs if s.get("status") == "confirmed" and s.get("token") and due(s, today)]
    confirmed.sort(key=lambda s: ((s.get("prefs") or {}).get("freq") != "daily", s.get("last") or ""))  # daily first, longest wait first
    for s in confirmed:
        hits = new_for(s, jobs)
        if hits and len(emails) >= cap:
            deferred += 1
            continue                      # keeps its old "last", so it goes out on the next run
        if hits:
            emails.append(build_email(s, hits))
        updates[s["email"]] = {**s, "last": today}
    return emails, updates, deferred


# ---------- Cloudflare KV and Resend ----------

def _req(url, token, data=None, method=None, raw=False):
    h = {"Authorization": f"Bearer {token}", "User-Agent": "ControlRolesBot/1.0"}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h, method=method or ("POST" if body else "GET"))
    with urllib.request.urlopen(req, timeout=60) as r:
        out = r.read().decode("utf-8")
    return out if raw else json.loads(out)


def kv_ids(token):
    acc = _req(f"{CF}/accounts?per_page=50", token)["result"][0]["id"]
    for ns in _req(f"{CF}/accounts/{acc}/storage/kv/namespaces?per_page=100", token)["result"]:
        if ns["title"] == KV_TITLE:
            return acc, ns["id"]
    raise SystemExit(f"KV namespace {KV_TITLE} not found: deploy the sign-up service first")


def load_subs(token, acc, ns):
    base = f"{CF}/accounts/{acc}/storage/kv/namespaces/{ns}"
    keys, cursor = [], ""
    while True:
        r = _req(f"{base}/keys?prefix=s:&limit=1000" + (f"&cursor={cursor}" if cursor else ""), token)
        keys += [k["name"] for k in r["result"]]
        cursor = (r.get("result_info") or {}).get("cursor") or ""
        if not cursor:
            break
    subs = []
    for k in keys:
        try:
            subs.append(json.loads(_req(f"{base}/values/{urllib.parse.quote(k, safe='')}", token, raw=True)))
        except Exception as e:
            print(f"::warning::could not read one subscriber: {e}")
    return subs


def save_subs(token, acc, ns, updates):
    if not updates:
        return
    base = f"{CF}/accounts/{acc}/storage/kv/namespaces/{ns}"
    items = []
    for email, s in updates.items():   # re-read first: someone may have unsubscribed or changed their alert meanwhile
        try:
            cur = json.loads(_req(f"{base}/values/{urllib.parse.quote('s:' + email, safe='')}", token, raw=True))
        except Exception:
            continue
        cur["last"] = s["last"]
        items.append({"key": "s:" + email, "value": json.dumps(cur)})
    for i in range(0, len(items), 1000):
        _req(f"{base}/bulk", token, items[i:i + 1000], method="PUT")


def send(emails, key):
    sent = 0
    for i in range(0, len(emails), 100):
        chunk = emails[i:i + 100]
        _req("https://api.resend.com/emails/batch", key, chunk)
        sent += len(chunk)
    return sent


def load_jobs():
    with open(os.path.join(ROOT, "data", "jobs.json"), encoding="utf-8") as f:
        return json.load(f)["jobs"]


def main(argv):
    dry = "--dry-run" in argv
    cf, rs = os.environ.get("CLOUDFLARE_API_TOKEN"), os.environ.get("RESEND_API_KEY")
    if not cf or not rs:
        print("Job alerts: not set up yet (CLOUDFLARE_API_TOKEN / RESEND_API_KEY missing). Nothing sent.")
        return 0
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    acc, ns = kv_ids(cf)
    subs = load_subs(cf, acc, ns)
    emails, updates, deferred = plan(subs, load_jobs(), today, DAILY_CAP)
    confirmed = sum(1 for s in subs if s.get("status") == "confirmed")
    print(f"Job alerts: {confirmed} confirmed subscribers, {len(subs) - confirmed} awaiting confirmation; "
          f"{len(emails)} emails to send, {deferred} held over to the next run.")
    if dry:
        for m in emails[:5]:
            print(" -", m["subject"])
        return 0
    if emails:
        send(emails, rs)
    save_subs(cf, acc, ns, updates)
    print(f"Job alerts: sent {len(emails)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
