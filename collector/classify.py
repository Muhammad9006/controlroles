"""Decide whether a job is relevant (project management family, construction and infrastructure) and tag it.
Jobs are kept worldwide; the country is worked out from the posting's country code, location text or title."""
import re

from .countries import ALIASES, AU_STATES, CA_PROVINCES, CITIES, CODES, COUNTRIES, REGION_NAMES, US_STATES

# Checked in order: first match wins. Patterns match job titles.
DISCIPLINES = [
    ("Claims", r"\bclaims?\b|\bdelay\b|\bforensic\b|\bdispute"),
    ("Cost & Commercial", r"quantity (audit|survey)|\bcosting\b|\bcost plann|pre[- ]?contract|post[- ]?contract|quantity surveyor|\bqs\b|\bcommercial (manager|director|lead|assurance)"),
    ("Contracts", r"\b(sub)?contracts?\b(?! ?engineer.*electrical)|\bsubcontract|\bcontract (manager|administrat)|\bprocurement manager"),
    ("Planning", r"\bplanner\b|\bplanning ?(engineer|manager|lead|director|specialist|control|and controls|& controls|/|head)|head of planning|charg[ée] (d.[ée]tude )?(de )?planification|"
                 r"engineer - planning|^planning\b|\bproject planning\b|manager[- ]+planning|\bmep planning|[-–] planning\b|\bscheduler\b|\bscheduling\b|\bschedule (manager|engineer)|\bplanificat"),
    ("Risk", r"\brisk (manager|engineer|lead|analyst|director|specialist)\b"),
    ("Project Controls", r"project controls?|\bpmo\b|\bearned value|\bcontrols (manager|lead|engineer)|\breporting manager"),
    ("Cost & Commercial", r"\bcost (manager|engineer|controller|control|consultant|lead)|\bestimat|\b[eé]conomiste\b|kalkulat"),
    ("Project Management", r"\bproject (manager|director|lead|surveyor)\b|\bprogram(me)? (manager|director|lead)\b|\bdevelopment (manager|director)\b|"
                           r"\bconstruction (manager|director)\b|director[- ]+construction|\bproject management\b|\bprojects? (manager|director|head)\b|manager[- ]+projects?\b|"
                           r"projects?[- ]execution head|\bfit[- ]?out manager|manager[- ]+fit[- ]?out|\bhandover\b|close-?out|head of projects?|\bvp,? project|vice president,? project|"
                           r"chef de projets?|directeur de (projets?|travaux)|conducteur de travaux|responsable (de )?travaux|kierownik|"
                           r"projektleiter|projektmanager|projektmanagement|responsable (de )?projets?|chef de mission"),
]
# Titles that look relevant but are not project-delivery roles.
EXCLUDE = (r"urban plann|master plann|transport plann|town plann|financial plann|\bfp&a\b|media plann|demand plann|"
           r"production plann|workforce plann|material plann|maintenance plann|supply chain plann|planificat\w*(?:\(\w+\))? de production|land use|environmental plann|"
           # outside construction & infrastructure: IT, software, life sciences, sales and marketing
           r"\bit (project|program|programme|service|infrastructure|pmo)|information technology|software|saas|cyber|"
           r"\bsap\b|\berp\b|data (scientist|engineer)|clinical trial|pharmacovigilance|pharmacist|scrum|agile coach|"
           r"digital (lead|transformation|delivery)|fare (system|collection)|transit technology|insurance|adjuster|credit risk|"
           r"wedding|event planner|account manager|\barmy\b|\bnavy\b|air force|military|"
           r"marketing|\bhr\b|human resources|sales|intern\b|internship|graduate|trainee|co-op|student(?! (accommodation|housing|residence))|"
           r"entry[- ]level|d[ée]butant|apprentice|"
           # planning roles that are town, policy or master planning rather than project planning
           r"landscape|development plann|policy|service planner|port planner|aviation plann|airport plann|aam planner|"
           r"water planning|planning consult|network planning|systems planning|transmission planning|distribution system|"
           r"operations planning|laboratory planning|resiliency planning|planning \+ urbanism|urbanism|geospatial|"
           r"planificat\w* aeroportuaire|programmation|"
           # other roles that only share a keyword
           r"document control|instrumentation|electrical controls|protection and controls|archaeolog|fire risk|"
           r"business development|business planning|legal|counsel|credit controller|benefits program|"
           r"expression of interest|join aecom|copy of|toll operator|rebates|unmanned|electronic security|"
           r"\bdefen[cs]e\b|recruit|university hire|new grad|administrative assistant|application support|\bai\b|material planner|workforce planner|lift planner|nnsa|"
           r"digital transformation|it strategy|"
           r"monitoring and control systems|chemical warfare|substantial damage|ceqa|remediation")

LEVELS = [("Director", r"\bdirector\b|\bhead\b|\bvp\b|vice president|\bchief\b|\bdirecteur\b|\bdirectrice\b|\bjefe\b"),
          ("Manager", r"\bmanager\b|leiter\b|\blead\b|\bprincipal\b|chef de projet|\bresponsable\b|\bkierownik\b|\bgerente\b"),
          ("Senior", r"\bsenior\b|\bsr\.?\b"),
          ("Mid", r".")]


def _name(token):
    t = token.strip().strip(".")
    if not t:
        return None
    if t.upper() == t and t.upper() in CODES and len(t) in (2, 3) and t.upper() != "NA":  # "NA" usually means not applicable
        return CODES[t.upper()]
    low = t.lower()
    if low in ALIASES:
        return ALIASES[low]
    for name in COUNTRIES:
        if low == name.lower():
            return name
    return None


def country_of(hint=None, location=None, title=None):
    """Website country name, or None if the posting doesn't say."""
    if hint:
        n = _name(hint) or _name(hint.upper())
        if n:
            return n
    parts = [p.strip() for p in re.split(r"[,/|]| - ", location or "") if p.strip()]
    blob = " " + " ".join(x for x in (location, title) if x).lower() + " "

    def city_country():
        for name, cities in CITIES.items():
            if any(re.search(r"\b" + re.escape(c) + r"\b", blob) for c in cities):
                return name
        return None
    for p in reversed(parts):
        low = p.lower()
        if low in AU_STATES:
            return "Australia"
        if len(parts) > 1 and len(p) == 2 and p.isupper():
            # 'Chicago, IL' / 'Calgary, AB': a state or province code, not a country code.
            # A known city elsewhere in the text wins (e.g. 'Perth, WA', 'Mumbai, IN').
            known = city_country()
            if known:
                return known
            if p in US_STATES or p in CA_PROVINCES:
                return "United States" if p in US_STATES else "Canada"
        n = _name(p)
        if n:
            return n
    for place, name in REGION_NAMES.items():
        if re.search(r"\b" + re.escape(place) + r"\b", blob):
            return name
    for name in COUNTRIES:
        if re.search(r"\b" + re.escape(name.lower()) + r"\b", blob):
            return name
    for alias, name in ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", blob):
            return name
    for name, cities in CITIES.items():
        if any(re.search(r"\b" + re.escape(c) + r"\b", blob) for c in cities):
            return name
    return None


def discipline_of(title):
    t = title.lower()
    if re.search(EXCLUDE, t):
        return None
    for name, pat in DISCIPLINES:
        if re.search(pat, t):
            return name
    return None


def level_of(title):
    t = title.lower()
    if re.search(r"\b(assistant|junior|jr|entry[- ]level)\b(?! (director|vice|principal|partner))", t) and not re.search(r"\bdirector\b|\bhead of\b", t):
        return "Mid"
    for name, pat in LEVELS:
        if re.search(pat, t):
            return name
    return "Mid"


def clean_title(title):
    """Remove internal codes some careers systems leave in titles, e.g. 'Job Title: ...', '(M3)', '(5990814)'."""
    t = re.sub(r"^\s*job title\s*:\s*", "", title or "", flags=re.I)
    t = re.sub(r"\s*\((?:[MP]\d|CAO\d+|\d{5,}|Q-CO|EOI|req\s*\d+)\)", "", t, flags=re.I)
    t = re.sub(r"\s*[-–|]?\s*\b[A-Z]{3,5}\d{2,}\b\s*$", "", t)
    return re.sub(r"\s+", " ", t).strip(" -–|,")
