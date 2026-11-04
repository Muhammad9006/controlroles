"""One job-id rule shared by the collector and any one-off imports, so saved jobs keep their ids."""
import re
import unicodedata


def slug(text):
    t = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t.replace("&", "and")).strip("-")


def job_id(employer, raw_id):
    return f"{slug(employer)}-{str(raw_id).strip().lower()}"
