"""One connector per careers system. Each returns a list of raw jobs:
{"id", "title", "location", "country_hint", "url", "posted"}  (posted = ISO date or "")
`fetch` is injected so tests can replay saved responses instead of calling the internet.
"""
from . import lever, oracle, smartrecruiters, workday, workable, greenhouse, jibe, peoplestrong, teamtailor

SYSTEMS = {
    "lever": lever.collect,
    "oracle": oracle.collect,
    "smartrecruiters": smartrecruiters.collect,
    "workday": workday.collect,
    "workable": workable.collect,
    "greenhouse": greenhouse.collect,
    "jibe": jibe.collect,
    "peoplestrong": peoplestrong.collect,
    "teamtailor": teamtailor.collect,
}

# Optional: fetch one posting's full text so its requirements can be read (collector/skills.py)
DESCRIBE = {name: mod.describe for name, mod in
            {"lever": lever, "oracle": oracle, "smartrecruiters": smartrecruiters, "workday": workday, "workable": workable, "jibe": jibe, "peoplestrong": peoplestrong, "teamtailor": teamtailor}.items()}
