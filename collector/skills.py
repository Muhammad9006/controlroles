"""Read the skills, certifications and years of experience a posting asks for.
The order of SKILLS must match the SKILLS list in site/index.html: a job's "sk" field is a base-36 bit mask of it."""
import re

SKILLS = [
    ("Primavera P6", r"primavera|\bp6\b"), ("MS Project", r"ms project|microsoft project"),
    ("Schedule risk analysis (PRA, Monte Carlo)", r"primavera risk|\bpra\b|monte carlo|@risk|safran|acumen"),
    ("Power BI", r"power ?bi"), ("Excel", r"\bexcel\b"), ("EcoSys", r"ecosys"), ("Oracle Unifier", r"unifier"),
    ("Aconex", r"aconex"), ("CostX / Candy", r"costx|cubit|\bcandy\b"), ("BIM", r"\bbim\b|revit|navisworks"),
    ("SAP", r"\bsap\b"), ("Earned value", r"earned value|\bevm\b"), ("Time impact analysis", r"time impact|\btia\b"),
    ("Delay analysis", r"delay analys|windows analys|as-planned|as-built"), ("EOT", r"extension of time|\beots?\b"),
    ("Claims", r"claim"), ("FIDIC", r"fidic"), ("NEC", r"\bnec\s?[34]?\b"), ("JCT", r"\bjct\b"),
    ("Contract administration", r"contract administration|contract management|contract admin"),
    ("Variations and change control", r"variation|change order|change management|change control"),
    ("Cost estimating", r"estimat"), ("Quantity take-off / BOQ", r"take-?off|bill of quantit|\bboq\b|\bbq\b"),
    ("Cost control and budgets", r"cost control|cost management|budget"), ("Cash flow forecasting", r"cash ?flow|forecast"),
    ("Procurement and tendering", r"procurement|tender"), ("Risk management", r"risk (management|register|analys|assessment)"),
    ("Baseline programme", r"baseline"), ("Critical path", r"critical path|\bcpm\b"),
    ("Progress reporting", r"progress report|monthly report|dashboard"), ("Look-ahead programmes", r"look-?ahead"),
    ("Stakeholder management", r"stakeholder"), ("Design management", r"design management|design review|design coordination"),
    ("MEP", r"\bmep\b"), ("Commissioning and handover", r"commissioning|handover|close-?out"),
    ("Value engineering", r"value engineering"), ("PMP", r"\bpmp\b"), ("PMI-SP / PMI-RMP", r"pmi-?sp|pmi-?rmp"),
    ("AACE (PSP, CCP)", r"aace|\bpsp\b|\bccp\b|\bevp\b"), ("RICS", r"\brics\b|mrics"), ("CIOB", r"\bciob\b|mciob"),
    ("Chartered engineer", r"chartered|\bceng\b|\bice\b"), ("Saudi Council of Engineers", r"saudi council|\bsce\b"),
    ("PRINCE2", r"prince ?2"), ("Arabic", r"arabic"), ("Bachelor's degree", r"bachelor|b\.?sc\b|degree in"),
    ("Master's degree", r"master'?s|\bm\.?sc\b|\bmba\b"), ("GCC experience", r"\bgcc\b|middle east|gulf region|saudi|\bksa\b"),
    # added Nov 2026 (keep at the end: the order is the bit position)
    ("French", r"\bfrench\b|fran[cç]ais"), ("Spanish", r"\bspanish\b|espa[nñ]ol"), ("German", r"\bgerman\b|deutsch"),
    ("Portuguese", r"portugu[eê]s"), ("Driving licence", r"driv(ing|er'?s) licen[cs]e"), ("4D planning (Synchro)", r"synchro|\b4d\b"),
    ("Diploma", r"\bdiploma\b|\bhnc\b|\bhnd\b"), ("NEC accreditation", r"nec (accredit|project manager accredit|ecc accredit)"),
    ("APM (PMQ, ChPP)", r"\bapm\b|\bpmq\b|chpp"), ("Project controls software (P6 / Unifier / EcoSys)", r"project controls (software|tools|systems)"),
]
_RES = [re.compile(p) for _, p in SKILLS]
_YEARS = re.compile(r"(\d{1,2})\s*\+?\s*(?:-|to)?\s*(?:\d{1,2}\s*)?\+?\s*(?:years|yrs)")
DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


def _base36(n):
    s = ""
    while True:
        n, r = divmod(n, 36)
        s = DIGITS[r] + s
        if not n:
            return s


_YR = r"(?:years|yrs)"
_RANGE = re.compile(r"(\d{1,2})\s*(?:-|–|—|to)\s*(\d{1,2})\s*\+?\s*" + _YR)
_MIN = re.compile(r"(?:minimum|min\.?|at least|over|more than|no less than)\s*(?:of\s*)?(\d{1,2})\s*\+?\s*" + _YR)
_PLAIN = re.compile(r"(\d{1,2})\s*\+?\s*" + _YR + r"[’']?\s*(?:of\s*)?(?:[a-z/&,-]+\s+){0,6}?(?:experience|exp\b)")
_PLUS = re.compile(r"(\d{1,2})\s*\+\s*" + _YR)
FIELDS = [("civil", r"civil"), ("mechanical", r"mechanical"), ("electrical", r"electrical"), ("qs", r"quantity survey"),
          ("construction", r"construction (management|engineering)|building"), ("architecture", r"architect"),
          ("pm", r"project management"), ("engineering", r"engineering"), ("business", r"business|finance|economics|commerce")]
_DEG = re.compile(r"(bachelor'?s?|b\.?\s?sc|b\.?\s?eng|\bb\.?e\b|\bb\.?tech|master'?s?|m\.?\s?sc|\bmba\b|\bphd\b|diploma|\bhnc\b|\bhnd\b|degree)")


def _clean(text):
    t = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"&nbsp;|&amp;|&#\d+;", " ", t).lower()


def years_of(t):
    """(minimum, maximum) years of experience asked for, (0, 0) when the posting does not say.
    The first figure in the text wins: postings state the overall requirement first and the
    narrower ones ("of which 5 in the GCC") after it."""
    ok = lambda n: 1 <= n <= 35
    found = []
    for m in _RANGE.finditer(t):
        a, b = int(m.group(1)), int(m.group(2))
        if ok(a) and ok(b) and a < b:
            found.append((m.start(), a, b))
    for rx in (_MIN, _PLUS, _PLAIN):
        for m in rx.finditer(t):
            a = int(m.group(1))
            if ok(a):
                found.append((m.start(), a, 0))
    if not found:
        return 0, 0
    _, lo, hi = min(found)
    return lo, hi


def degree_of(t):
    """'B:civil,qs' style code: level B (bachelor/degree), M (master), D (diploma) and up to 3 subjects."""
    found = list(_DEG.finditer(t))
    if not found:
        return ""
    words = [m.group(1) for m in found]
    # the lowest level that is accepted: "diploma or degree" -> D; "bachelor's, master's preferred" -> B
    lvl = "D" if any(w.startswith(("diploma", "hn")) for w in words) else "B" if any(w.startswith(("bachelor", "b", "degree")) for w in words) else "M"
    near = " ".join(t[m.end():m.end() + 90] for m in found)
    subj = [c for c, r in FIELDS if re.search(r, near)]
    if "engineering" in subj and len(subj) > 1:
        subj.remove("engineering")
    return lvl + (":" + ",".join(subj[:3]) if subj else "")


def read_full(text):
    """Everything the board shows about a posting's requirements."""
    t = _clean(text)
    out = {}
    mask = sum(1 << i for i, r in enumerate(_RES) if r.search(t))
    if mask:
        out["sk"] = _base36(mask)
    lo, hi = years_of(t)
    if lo:
        out["yrs"] = lo
    if hi:
        out["yrsMax"] = hi
    deg = degree_of(t)
    if deg:
        out["deg"] = deg
    return out


def read(text):
    """(mask in base 36, minimum years or 0) for a posting's text."""
    f = read_full(text)
    return f.get("sk", ""), f.get("yrs", 0)


def labels(mask36):
    m = int(mask36, 36) if mask36 else 0
    return [name for i, (name, _) in enumerate(SKILLS) if m >> i & 1]
