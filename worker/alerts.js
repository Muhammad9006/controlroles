// ControlRoles job-alert sign-ups (Cloudflare Worker, free plan).
// POST /subscribe      save a sign-up and email a confirmation link (double opt-in)
// GET  /confirm        confirm the email address and switch the alert on
// GET  /unsubscribe    show an unsubscribe button; POST /unsubscribe removes the alert (also one-click from mail apps)
// Subscribers live in the KV namespace SUBS under "s:<email>". The robot (collector/alerts.py) reads them,
// matches each day's new roles and sends the alert emails.
// Secret: RESEND_API_KEY (set by .github/workflows/alerts-service.yml).

const SITE = "https://controlroles.com";
const API = "https://api.controlroles.com";
const FROM = "ControlRoles <alerts@controlroles.com>";
const REPLY_TO = "hello@controlroles.com";
const DISCS = ["Planning", "Project Controls", "Cost & Commercial", "Contracts", "Claims", "Risk", "Project Management"];
const LEVELS = ["Mid", "Senior", "Manager", "Director"];
const CONFIRM_CAP = 30;          // confirmation emails a day (the free email plan sends 100 a day in total)
const ORIGINS = [SITE, "https://www.controlroles.com", "https://muhammad9006.github.io"];

const today = () => new Date().toISOString().slice(0, 10);
const daysAgo = n => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const clip = (s, n = 60) => String(s ?? "").trim().slice(0, n);

function cors(req) {
  const o = req.headers.get("Origin") || "";
  return {
    "Access-Control-Allow-Origin": ORIGINS.includes(o) ? o : SITE,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept",
    "Vary": "Origin",
  };
}
const json = (req, body, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...cors(req) } });

function page(title, body, status = 200) {
  return new Response(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>${esc(title)} · ControlRoles</title>
<style>body{margin:0;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#F1F4F6;color:#0B1D22}
main{max-width:520px;margin:12vh auto;padding:28px 24px;background:#fff;border:1px solid #CFDCDF;border-radius:16px}
h1{font-size:22px;margin:0 0 10px}p{margin:0 0 14px;color:#3D5359}a{color:#0A707A;font-weight:600}
.brand{font-weight:800;color:#0B1D22;text-decoration:none;display:inline-block;margin-bottom:18px}.brand span{color:#0A707A}
button{font:inherit;font-weight:700;background:#0B5E66;color:#fff;border:0;border-radius:10px;padding:11px 18px;cursor:pointer}</style></head>
<body><main><a class="brand" href="${SITE}">Control<span>Roles</span></a><h1>${esc(title)}</h1>${body}</main></body></html>`,
    { status, headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" } });
}

function cleanPrefs(b) {
  let disc = b.disc;
  if (typeof disc === "string") disc = disc.split(",");
  disc = Array.isArray(disc) ? disc.map(x => String(x).trim()).filter(x => DISCS.includes(x)) : [];
  const level = LEVELS.includes(b.level) ? b.level : "";
  const freq = b.freq === "daily" || b.pro === true || b.pro === "true" ? "daily" : "weekly";
  return { disc: [...new Set(disc)], region: clip(b.region), country: clip(b.country), level, freq };
}

function describe(p) {
  const bits = [p.disc.length ? p.disc.join(", ") : "All disciplines", p.country || p.region || "Worldwide", p.level || "All levels"];
  return `${bits.join(" · ")} · ${p.freq === "daily" ? "daily" : "weekly"} email`;
}

async function sendEmail(env, msg) {
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from: FROM, reply_to: REPLY_TO, ...msg }),
  });
  if (!r.ok) throw new Error(`email ${r.status} ${await r.text()}`);
}

async function subscribe(req, env) {
  let b;
  try { b = await req.json(); } catch { return json(req, { ok: false, error: "bad request" }, 400); }
  if (b.website) return json(req, { ok: true, status: "pending" });            // hidden field: only bots fill it in
  const email = String(b.email || "").trim().toLowerCase();
  if (email.length > 254 || !/^[^\s@<>"',;]+@[^\s@<>"',;]+\.[a-z]{2,}$/i.test(email)) return json(req, { ok: false, error: "Please enter a valid email address." }, 400);
  const prefs = cleanPrefs(b);
  const key = "s:" + email;
  const s = (await env.SUBS.get(key, "json")) || { email, status: "pending", created: new Date().toISOString() };
  const same = s.prefs && JSON.stringify(s.prefs) === JSON.stringify(prefs);
  if (s.status === "confirmed" && same) return json(req, { ok: true, status: "confirmed" });
  if (s.sentAt && Date.now() - Date.parse(s.sentAt) < 10 * 60e3 && JSON.stringify(s.pending) === JSON.stringify(prefs))
    return json(req, { ok: true, status: "pending" });                      // a confirmation went out minutes ago
  const ck = "c:" + today(), count = +(await env.SUBS.get(ck)) || 0;
  if (count >= CONFIRM_CAP) return json(req, { ok: false, error: "We've had a lot of sign-ups today. Please try again tomorrow." }, 429);
  s.token = s.token || crypto.randomUUID().replace(/-/g, "");
  s.pending = prefs;
  s.sentAt = new Date().toISOString();
  const link = `${API}/confirm?e=${encodeURIComponent(email)}&t=${s.token}`;
  try {
    await sendEmail(env, {
      to: [email],
      subject: "Confirm your ControlRoles job alert",
      html: `<div style="font:15px/1.6 Arial,sans-serif;color:#0B1D22;max-width:560px">
<p style="font-size:18px;font-weight:800;margin:0 0 16px">Control<span style="color:#0A707A">Roles</span></p>
<p>Please confirm your job alert:</p><p style="background:#F1F4F6;border-radius:10px;padding:12px 14px">${esc(describe(prefs))}</p>
<p><a href="${link}" style="display:inline-block;background:#0B5E66;color:#fff;text-decoration:none;font-weight:700;border-radius:10px;padding:12px 20px">Confirm my alert</a></p>
<p style="color:#3D5359;font-size:13px">If you didn't ask for this, ignore this email and you won't hear from us.</p></div>`,
      text: `Please confirm your ControlRoles job alert (${describe(prefs)}):\n${link}\n\nIf you didn't ask for this, ignore this email.`,
    });
  } catch (e) {
    console.log(String(e));
    return json(req, { ok: false, error: "Sorry, your alert couldn't be saved. Please try again in a minute." }, 502);
  }
  await env.SUBS.put(key, JSON.stringify(s));
  await env.SUBS.put(ck, String(count + 1), { expirationTtl: 3 * 86400 });
  return json(req, { ok: true, status: "pending" });
}

async function confirm(url, env) {
  const email = (url.searchParams.get("e") || "").toLowerCase(), t = url.searchParams.get("t") || "";
  const s = email && (await env.SUBS.get("s:" + email, "json"));
  if (!s || !t || s.token !== t) return page("This link has expired", `<p>Please set up your alert again on <a href="${SITE}/#alerts">ControlRoles</a>.</p>`, 400);
  if (s.pending) { s.prefs = s.pending; delete s.pending; }
  if (s.status !== "confirmed" || !s.last) s.last = daysAgo(s.prefs.freq === "daily" ? 1 : 7);
  s.status = "confirmed";
  s.confirmedAt = new Date().toISOString();
  await env.SUBS.put("s:" + email, JSON.stringify(s));
  const when = s.prefs.freq === "daily" ? "tomorrow" : "within a week";
  return page("Your job alert is on", `<p><b>${esc(describe(s.prefs))}</b></p><p>Your first email with new matching roles arrives ${when}. Every email has an unsubscribe link.</p><p><a href="${SITE}/#jobs">Browse roles now →</a></p>`);
}

async function unsubscribe(req, url, env) {
  const email = (url.searchParams.get("e") || "").toLowerCase(), t = url.searchParams.get("t") || "";
  const s = email && (await env.SUBS.get("s:" + email, "json"));
  const valid = s && t && s.token === t;
  if (req.method === "POST") {
    if (valid) await env.SUBS.delete("s:" + email);
    return page("You're unsubscribed", `<p>${esc(email)} won't get any more job alerts from us.</p><p>Changed your mind? <a href="${SITE}/#alerts">Set up a new alert</a>.</p>`);
  }
  if (!valid) return page("You're unsubscribed", `<p>This address isn't signed up for any alerts.</p><p><a href="${SITE}/#alerts">Set up an alert</a></p>`);
  return page("Unsubscribe from job alerts?", `<p>${esc(email)} will stop getting ControlRoles job alerts.</p>
<form method="post" action="${API}/unsubscribe?e=${encodeURIComponent(email)}&t=${esc(t)}"><button type="submit">Unsubscribe</button></form>`);
}


// ---- "applied via ControlRoles" counts: one per visitor per job, kept for 90 days ----
async function applyClick(req, env) {
  let b; try { b = await req.json(); } catch { return json(req, { ok: false }, 400); }
  const id = clip(b.id, 120), v = clip(b.v, 40);
  if (!id || !/^[\w-]{8,40}$/.test(v)) return json(req, { ok: false }, 400);
  const seen = "v:" + id + ":" + v;
  const counts = (await env.SUBS.get("applycounts", "json")) || {};
  if (await env.SUBS.get(seen)) return json(req, { ok: true, n: counts[id] || 0 });
  counts[id] = (counts[id] || 0) + 1;
  await env.SUBS.put(seen, "1", { expirationTtl: 90 * 86400 });
  await env.SUBS.put("applycounts", JSON.stringify(counts));
  return json(req, { ok: true, n: counts[id] });
}
async function applyCounts(req, env) {
  const counts = (await env.SUBS.get("applycounts", "json", { cacheTtl: 60 })) || {};
  return new Response(JSON.stringify(counts), { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=60", ...cors(req) } });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    try {
      if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(req) });
      if (url.pathname === "/subscribe" && req.method === "POST") return await subscribe(req, env);
      if (url.pathname === "/apply" && req.method === "POST") return await applyClick(req, env);
      if (url.pathname === "/applies" && req.method === "GET") return await applyCounts(req, env);
      if (url.pathname === "/confirm" && req.method === "GET") return await confirm(url, env);
      if (url.pathname === "/unsubscribe") return await unsubscribe(req, url, env);
      if (url.pathname === "/") return Response.redirect(SITE + "/#alerts", 302);
      return new Response("Not found", { status: 404 });
    } catch (e) {
      console.log(String(e && e.stack || e));
      return url.pathname === "/subscribe" ? json(req, { ok: false, error: "Sorry, something went wrong. Please try again." }, 500)
        : page("Something went wrong", `<p>Please try again in a minute, or email <a href="mailto:${REPLY_TO}">${REPLY_TO}</a>.</p>`, 500);
    }
  },
};
