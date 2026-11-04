"""Tiny HTTP helper with retries. Uses only the Python standard library."""
import json
import time
import urllib.error
import urllib.request

UA = "ControlRolesBot/1.0 (+https://controlroles.com; hello@controlroles.com)"


def get_text(url, tries=3, timeout=30):
    """Plain-text GET (RSS feeds) with the same retry rules as get_json."""
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            last = e
            if 400 <= e.code < 500 and e.code != 429:
                raise
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise last


def get_json(url, data=None, headers=None, tries=3, timeout=30):
    body = json.dumps(data).encode() if data is not None else None
    h = {"User-Agent": UA, "Accept": "application/json"}
    if body is not None:
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers=h, method="POST" if body is not None else "GET")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:  # 4xx (wrong settings, closed job) will not fix itself: stop at once
            last = e
            if 400 <= e.code < 500 and e.code != 429:
                raise
        except Exception as e:  # network errors, server errors, bad JSON
            last = e
            time.sleep(2 * (attempt + 1))
    raise last
