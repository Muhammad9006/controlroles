"""Facts a job seeker needs before applying, read from the job title and the posting text.

- elig:   who can apply. Codes: nat (nationals only), citizen (citizens / permanent residents only),
          clearance (security clearance), nosponsor (no visa sponsorship / right to work required),
          sponsor (visa sponsorship offered), chartered (chartered status or professional licence).
- pay:    [min, max, currency, per] when the posting states pay, e.g. [95000, 120000, "USD", "year"].
- sector: list of sector codes (see SECTORS).
- ben:    list of benefit codes the posting mentions (see BENEFITS), e.g. ["housing", "flights", "medical"].
- leave:  annual leave in days when the posting states it, e.g. 30.

Only what the posting itself says is recorded; nothing is guessed. Keep the codes in step with site/index.html.
"""
import re

ELIG = [
    # exclusive wording only ("only", "must be", "required", "restricted to"), or the title pattern "(Saudi National)"
    ("nat", r"\((saudi|emirati|uae|qatari|omani|kuwaiti|bahraini)\s+nationals?\)|[-–]\s*(saudi|emirati|uae|qatari|omani|kuwaiti|bahraini)\s+nationals?\s*$|"
            r"\b(saudi|emirati|uae|qatari|omani|kuwaiti|bahraini)\s+nationals?\s+only\b|\bnationals?\s+only\b|\bsaudis?\s+only\b|"
            r"\b(only|exclusively|restricted to|reserved for|open only to)\s+(for\s+)?(saudi|emirati|uae|qatari|omani|kuwaiti|bahraini)\s+(nationals?|citizens?)\b|"
            r"\bmust be (a\s+)?(saudi|emirati|uae|qatari|omani|kuwaiti|bahraini)\s+(national|citizen)\b|"
            r"\b(saudi|emirati|uae|qatari|omani|kuwaiti|bahraini)\s+(nationality|national|citizenship)\s+(is\s+)?(required|mandatory)\b"),
    ("citizen", r"\bmust be an? (u\.?s\.?|us|american|canadian|australian)?\s*citizen\b|"
                r"\b(u\.?s\.?|us|american|canadian|australian)\s+citizenship\s+(is\s+)?(required|mandatory)\b|"
                r"\bcitizenship (is )?required\b|\b(only|restricted to)\s+(u\.?s\.?|us|canadian|australian)\s+citizens\b|"
                r"\b(u\.?s\.?|us|canadian|australian)\s+citizens?\s+only\b"),
    ("clearance", r"\b(security|secret|top secret|ts/sci|sc|dv|nv1|nv2|baseline|government) clearance\b|"
                  r"\bpublic trust\b|\bclearance (is )?required\b|\babl(e)? to obtain .{0,20}clearance\b"),
    ("nosponsor", r"\b(no|not|unable to|cannot|can ?not|will not|won'?t|does not|do not|not able to)\s+(be able to\s+)?(provide|offer|support)?\s*"
                  r"(visa\s+|work\s+)?(sponsor|sponsorship)\b|\bwithout (the need for )?(visa )?sponsorship\b|"
                  r"\b(must not|will not|does not) require (visa |work )?sponsorship\b|"
                  r"\bsponsorship (is )?not (available|provided|offered)\b|\bmust have (the )?(full )?right to work\b|"
                  r"\bright to work in the (uk|united kingdom|us|australia) (is )?required\b"),
    ("sponsor", r"\bvisa sponsorship (is )?(available|provided|offered|possible)\b|\bwe (can|will|are able to) sponsor\b|"
                r"\bsponsorship (is )?available\b|\bwill sponsor\b"),
    ("chartered", r"\bchartered\b|\bmrics\b|\bmciob\b|\bceng\b|\bp\.?\s?e\.? licen[cs]e\b|\blicen[cs]ed professional engineer\b|"
                  r"\bregistered professional engineer\b|\bsaudi council of engineers\b|\bsce (accreditation|membership|registration)\b"),
]
# softening words right after a match ("Saudi nationals preferred / encouraged / and expats") cancel it
SOFT = re.compile(r"^\W{0,3}(are\s+|is\s+)?(preferred|encouraged|welcome|desirable|an advantage|a plus|and expat|& expat|or expat|and non)")

_ELIG = [(c, re.compile(p)) for c, p in ELIG]


def _hit(rx, low):
    for m in rx.finditer(low):
        if not SOFT.match(low[m.end():m.end() + 40]):
            return True
    return False

SECTORS = [
    ("datacentre", r"data ?cent(er|re)s?\b|hyperscale|\bdc\d?\b"),
    ("rail", r"\brail|\bmetro\b|\btransit\b|\btrains?\b|light rail|\blrt\b|high speed"),
    ("roads", r"highway|\broads?\b|bridges?\b|tunnel|motorway"),
    ("aviation", r"airport|aviation|airside|(passenger|airport) terminal"),
    ("water", r"wastewater|\bwater\b(?! injection)|desalination|water utilit"),
    ("energy", r"\bpower\b(?!\s?bi)|\benergy\b|renewable|solar|\bwind\b|substation|transmission line|nuclear|\bbess\b"),
    ("oilgas", r"\boil\b|\bgas\b|\blng\b|petrochem|refiner|offshore|onshore|hydrocarbon|pipeline"),
    ("buildings", r"\bbuildings?\b(?! information)|residential|commercial (building|real estate|development|tower|fit[- ]?out)|hospital|healthcare|\bschools?\b|university|office tower|mixed[- ]use"),
    ("hospitality", r"hotel|hospitality|resort|palace|leisure|entertainment"),
    ("industrial", r"factor(y|ies)|industrial|manufactur|mining|minerals|metals"),
]
_SECT = [(c, re.compile(p)) for c, p in SECTORS]
BODY_OK = {"datacentre", "rail", "aviation", "water", "energy", "oilgas"}  # words too common to trust in a body: buildings, roads...

_CUR = {"$": "USD", "us$": "USD", "usd": "USD", "£": "GBP", "gbp": "GBP", "€": "EUR", "eur": "EUR", "sar": "SAR",
        "aed": "AED", "qar": "QAR", "cad": "CAD", "c$": "CAD", "aud": "AUD", "a$": "AUD", "inr": "INR", "₹": "INR"}
_NUM = r"(\d{1,3}(?:[,\s]\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*(k|K)?(?![\d,])"
_PAY = re.compile(r"(us\$|c\$|a\$|\$|£|€|₹|usd|gbp|eur|sar|aed|qar|cad|aud|inr)\s?" + _NUM +
                  r"(?:\s*(?:-|–|—|to)\s*(?:us\$|c\$|a\$|\$|£|€|₹|usd|gbp|eur|sar|aed|qar|cad|aud|inr)?\s?" + _NUM + r")?"
                  r"(?:\s*(?:(?:per|/|an|a)\s*(hour|hr|day|month|year|annum|yr)|(hourly|daily|monthly|annually|yearly)))?"
                  r"(?!\s*(?:million|bn|billion|m\b|per diem))", re.I)
_PAYWORD = re.compile(r"salary|pay|compensation|remuneration|rate|wage|package|base|ote|earn", re.I)


def _num(s, k):
    v = float(re.sub(r"[,\s]", "", s))
    return v * 1000 if k else v


def _pay(text):
    for m in _PAY.finditer(text):
        cur = _CUR.get(m.group(1).lower())
        lo = _num(m.group(2), m.group(3))
        hi = _num(m.group(4), m.group(5)) if m.group(4) else lo
        per = (m.group(6) or m.group(7) or "").lower()
        per = {"hr": "hour", "annum": "year", "yr": "year", "hourly": "hour", "daily": "day", "monthly": "month",
               "annually": "year", "yearly": "year"}.get(per, per)
        if not _PAYWORD.search(text[max(0, m.start() - 60):m.start()]):
            continue  # amounts not introduced as pay (budgets, project values, allowances)
        if not per:
            tail = text[m.end():m.end() + 45].lower()
            per = "month" if re.search(r"month", tail) else "year" if re.search(r"year|annum|annual|p\.a\.", tail) else ""
        if not per:
            per = "year" if lo >= 20000 else "hour" if lo < 400 else ""
        if not per or hi < lo:
            continue
        ok = {"year": 15000 <= lo <= 1500000, "month": 1500 <= lo <= 150000,
              "day": 100 <= lo <= 5000, "hour": 15 <= lo <= 600}[per] if per in ("year", "month", "day", "hour") else False
        if ok and hi <= lo * 3:
            return [int(lo), int(hi), cur, per]
    return None


# benefits: only what the posting says it offers (keep the codes in step with site/index.html)
BENEFITS = [
    ("inclusive", r"all[- ]inclusive|inclusive of (all )?(the )?allowances|(package|salary) (is )?inclusive|including (housing|accommodation) (and transport(ation)? )?allowances?|allowances? (are )?included"),
    ("housing", r"housing allowance|accommodation (allowance|provided)|(company|free|furnished|family) (housing|accommodation)|housing (is )?provided|rent allowance"),
    ("transport", r"transport(ation)? allowance|car allowance|company (car|vehicle)|vehicle allowance|fuel allowance|travel allowance"),
    ("flights", r"(annual|yearly|home|return) (air ?)?(ticket|flight|airfare|leave ticket)s?|air tickets?|annual airfare|flights? home"),
    ("medical", r"medical (insurance|cover|coverage|plan|benefits?)|health (insurance|cover|coverage|plan|care benefits?)|private (health|medical)|dental|vision (insurance|plan)"),
    ("family", r"family (status|visa|sponsorship|medical|package)|dependants?'? (visa|medical|cover)|for (you and )?your family|family (allowance|benefits)"),
    ("education", r"(school|education|tuition) (fees?|allowance|assistance|support|reimbursement)|children'?s education"),
    ("bonus", r"\bbonus(es)?\b|incentive (plan|scheme|pay)|profit[- ]shar"),
    ("pension", r"\bpension\b|401\(?k\)?|retirement (plan|savings|benefits?)|superannuation|provident fund|\brrsp\b|matching contributions?"),
    ("eosb", r"end[- ]of[- ]service|gratuity"),
    ("leave", r"annual leave|paid time off|\bpto\b|holiday entitlement|vacation (days|time|leave)|days'? (paid )?(holiday|leave)"),
    ("relocation", r"relocation (allowance|assistance|support|package|benefits?)|relocation (is )?(provided|available|offered)|mobilisation allowance"),
    ("hybrid", r"hybrid (work|working|role|model|schedule|arrangement)|flexible working|work from home|remote working|flexible hours"),
    ("rotation", r"\brotation(al)?\b (schedule|roster|basis|pattern)|\b\d{1,2} ?(x|/|on ?/ ?) ?\d{1,2}\b ?(rotation|roster|swing)|fly[- ]in[- ]fly[- ]out|\bfifo\b"),
    ("training", r"(professional|career) development|training (and|&) development|chartership|(membership|professional) (fees|subscriptions?)|tuition reimbursement|learning (budget|allowance)"),
    ("life", r"life (insurance|assurance|cover)|death in service"),
    ("shares", r"(employee )?(share|stock) (purchase|ownership|plan|scheme)|\bespp\b|employee[- ]owned"),
]
_BEN = [(c, re.compile(p)) for c, p in BENEFITS]
_LEAVE = re.compile(r"(\d{2})\s*(working |calendar )?days'?\s*(of\s*)?(paid\s*)?(annual leave|holiday|vacation|leave|pto)|(annual leave|holiday|vacation|pto)\s*(of|:)?\s*(\d{2})\s*(working |calendar )?days")
# phrases that describe what the CANDIDATE needs, not what is offered ("experience with pension schemes")
_BEN_NOT = re.compile(r"(experience|knowledge|understanding|administ\w*|manage\w*|advis\w*|process\w*) (in|of|with|on)? ?(the )?(pension|payroll|benefits|insurance|bonus)")


def _benefits(body):
    low = body.lower()
    low = _BEN_NOT.sub(" ", low)
    ben = [c for c, r in _BEN if r.search(low)]
    leave = None
    m = _LEAVE.search(low)
    if m:
        d = int(m.group(1) or m.group(8))
        if 15 <= d <= 45:
            leave = d
    return ben, leave


def _clean(text):
    t = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"&nbsp;|&amp;|&#\d+;", " ", t)


def read(title, text=""):
    """Facts from a title and (optionally) the posting text."""
    body = _clean(text)
    low = (title + " \n " + body).lower()
    elig = [c for c, r in _ELIG if _hit(r, low)]
    if "sponsor" in elig and "nosponsor" in elig:
        elig.remove("sponsor")
    # sector from the title first (more reliable); the body only adds a sector when the title names none
    sect = [c for c, r in _SECT if r.search(title.lower())] or \
        [c for c, r in _SECT if c in BODY_OK and len(r.findall(body.lower())) >= 2]
    out = {}
    if elig:
        out["elig"] = elig
    if sect:
        out["sector"] = sect[:2]
    pay = _pay(body) if body else None
    if pay:
        out["pay"] = pay
    if body:
        ben, leave = _benefits(body)
        if ben:
            out["ben"] = ben
        if leave:
            out["leave"] = leave
    return out
