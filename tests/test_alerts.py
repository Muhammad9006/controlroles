from collector import alerts

JOBS = [
    {"id": "a-1", "title": "Senior Planner", "emp": "AECOM", "disc": "Planning", "region": "GCC", "country": "Saudi Arabia", "city": "Riyadh", "level": "Senior", "firstSeen": "2026-11-04", "posted": "2026-11-03"},
    {"id": "a-2", "title": "Planning Manager", "emp": "WSP", "disc": "Planning", "region": "GCC", "country": "UAE", "city": "Dubai", "level": "Manager", "firstSeen": "2026-11-02", "posted": "2026-11-01"},
    {"id": "a-3", "title": "Cost Manager", "emp": "JLL", "disc": "Cost & Commercial", "region": "Europe", "country": "UK", "city": "London", "level": "Manager", "firstSeen": "2026-11-04", "posted": "2026-11-04"},
    {"id": "a-4", "title": "<b>Planner</b>", "emp": "X & Y", "disc": "Planning", "region": "GCC", "country": "Saudi Arabia", "city": "Jeddah", "level": "Mid", "firstSeen": "2026-10-20", "posted": "2026-10-20"},
]


def sub(email="a@b.com", freq="daily", last="2026-11-03", **p):
    prefs = {"disc": ["Planning"], "region": "GCC", "country": "", "level": "", "freq": freq, **p}
    return {"email": email, "status": "confirmed", "token": "t0k", "prefs": prefs, "last": last}


def test_matching_and_new_since_last():
    hits = alerts.new_for(sub(), JOBS)
    assert [j["id"] for j in hits] == ["a-1"]
    assert [j["id"] for j in alerts.new_for(sub(last="2026-11-01"), JOBS)] == ["a-1", "a-2"]
    assert [j["id"] for j in alerts.new_for(sub(last="2026-11-01", country="UAE"), JOBS)] == ["a-2"]
    everything = sub(last="2026-01-01", disc=[], region="")
    assert len(alerts.new_for(everything, JOBS)) == 4


def test_due_daily_and_weekly():
    assert alerts.due(sub(last="2026-11-03"), "2026-11-04")
    assert not alerts.due(sub(last="2026-11-04"), "2026-11-04")
    assert not alerts.due(sub(freq="weekly", last="2026-10-30"), "2026-11-04")
    assert alerts.due(sub(freq="weekly", last="2026-10-28"), "2026-11-04")


def test_plan_caps_and_skips():
    subs = [sub("d@x.com"), sub("w@x.com", freq="weekly", last="2026-10-01"), sub("none@x.com", disc=["Risk"]),
            {**sub("p@x.com"), "status": "pending"}]
    emails, updates, deferred = alerts.plan(subs, JOBS, "2026-11-04", cap=1)
    assert [m["to"][0] for m in emails] == ["d@x.com"]          # daily goes first
    assert deferred == 1 and "w@x.com" not in updates            # held over, keeps its old date
    assert updates["none@x.com"]["last"] == "2026-11-04"         # nothing new: clock moves on, no email
    assert "p@x.com" not in updates                               # unconfirmed: never emailed


def test_email_is_escaped_and_has_unsubscribe():
    m = alerts.build_email(sub(last="2026-01-01"), alerts.new_for(sub(last="2026-01-01"), JOBS))
    assert "<b>Planner</b>" not in m["html"] and "&lt;b&gt;Planner&lt;/b&gt;" in m["html"]
    assert "X &amp; Y" in m["html"]
    assert "api.controlroles.com/unsubscribe?e=a%40b.com&amp;t=t0k" in m["html"]
    assert m["headers"]["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert m["subject"] == "3 new Planning roles in GCC"
    assert "disc=Planning" in m["text"] and "region=GCC" in m["text"]


def test_no_keys_means_no_sending(monkeypatch, capsys):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    assert alerts.main([]) == 0
    assert "not set up yet" in capsys.readouterr().out


def test_morning_brief_builds():
    from collector import brief
    data = {"totals": [["date_range_0", 120, 90, 150, 600, 0.62, 95.0], ["date_range_1", 80, 60, 100, 400, 0.5, 80.0]],
            "week": [["20261029", 10], ["20261104", 120]],
            "channels": [["Organic Social", 60, 70], ["Direct", 40, 50]],
            "sources": [["linkedin.com", "referral", 55]], "countries": [["Saudi Arabia", 70], ["United Arab Emirates", 20]],
            "devices": [["mobile", 90], ["desktop", 30]], "pages": [["/jobs", 300], ["/job/a-1", 25]],
            "events": [["apply_click", 14], ["share", 3]]}
    s, h, t = brief.build(data, JOBS, "2026-11-04")
    assert s.startswith("ControlRoles brief · 2026-11-04: 120 visitors (+50%")
    assert "Organic Social (50%)" in h and "Senior Planner · AECOM" in h and "14 Apply clicks" in h and "75% of visitors were on a phone" in h
    assert "Saudi Arabia: 70" in t
    s2, _, _ = brief.build({}, JOBS, "2026-11-04")
    assert "0 visitors" in s2
