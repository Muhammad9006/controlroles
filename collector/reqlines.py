"""Pick the requirement lines out of a posting: the short sentences that say what the candidate needs
(experience, qualifications, certificates, software, knowledge). Shown on the job page under "Requirements"."""
import html
import re

CUE = re.compile(r"\b(\d{1,2}\s*\+?\s*(?:-|–|to)?\s*\d{0,2}\s*\+?\s*(?:years|yrs)|experience (in|with|of|on)|degree|bachelor|master'?s|diploma|qualif|chartered|certif|licen[cs]|membership|"
                 r"proficien|knowledge of|familiar|expertise|ability to|must (have|be)|required|essential|"
                 r"primavera|\bp6\b|fidic|\bnec\b|\bpmp\b|rics|ciob|aace|power bi|excel|arabic|english)", re.I)
STRONG = re.compile(r"(\d{1,2}\s*\+?\s*(?:-|–|to)?\s*\d{0,2}\s*\+?\s*(?:years|yrs)|degree|bachelor|master'?s|diploma|qualif|chartered|certif|licen[cs]|membership|accredit|"
                    r"proficien|knowledge of|familiar|experience (in|with|of|on)|primavera|\bp6\b|fidic|\bnec\d?\b|\bpmp\b|rics|ciob|aace|arabic)", re.I)
DUTY = re.compile(r"^(support|lead|maintain|manage|prepare|coordinate|provide|providing|develop|ensure|monitor|review|assist|deliver|drive|undertake|"
                  r"work|act|attend|liaise|produce|track|report|oversee|participate|conduct|facilitate|implement|establish|identify|create|compile|"
                  r"your daily|you will be|the role|responsible)\b", re.I)
NOISE = re.compile(r"(for our people|we strong|culture|salary|disclosure|onboarding|award-winning|our values|compensation|pay transparency|equal opportunit|apply now|privacy|cookie|recruit(ment)? agenc|diversity|accommodation request|we are an? |our company|about us|benefits? (include|package)|salary range|pay range|\bwe offer\b|click|disabilit|veteran|background check|drug|additional responsibilities|as required by (the )?business|official job listings|#li-|job listings here|perform other duties|other duties as assigned)", re.I)
TAG = re.compile(r"</?[a-z]+[^>]*>|\b(?:span|li|ul|ol|div|strong|em|br|font|p)\b(?:\s+[a-z-]+=\"[^\"]*\")+|/(?:span|li|ul|ol|div|strong|em|p)\b|\b(?:mso|lang|style|class)[-a-z]*=\"[^\"]*\"", re.I)


def clean(text):
    t = html.unescape(text or "")
    t = re.sub(r"</(?:li|p|div|h\d|tr)>|<br\s*/?>", " • ", t, flags=re.I)  # keep the posting's own line breaks
    t = TAG.sub(" ", t)
    t = re.sub(r"\b[a-z-]+='[^']*'", " ", t)                                    # single-quoted attributes
    t = re.sub(r"(?i)\b(?:margin|padding|font-[a-z]+|color|text-align|line-height|text-indent|white-space|-webkit-[a-z-]+)\s*:\s*[^;'\"•]*;?", " ", t)
    t = re.sub(r"(?<![\w'’])/(?:b|i|u|h[1-6]|H[1-6]|div|span|li|ul|ol|p|strong|em|font)\b", " ", t)   # "/b", "/H2"
    t = re.sub(r"(?<![\w'’-])(?:b|br|div|span|li|ul|ol|strong|em|font|H[1-6]|h[1-6])(?![\w'’-])", " ", t)  # bare tag words
    t = re.sub(r"\b/?(?:strong|em|span|li|ul|ol|p|br)\b(?=\s+[A-Z(:])", " ", t)
    t = re.sub(r"\b(?:s?pan|tyle|lass|ang)\b(?=\s+[A-Z])", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


HEAD = re.compile(r"^(?:(?:minimum|required|preferred|essential|desirable|basic|key)?\s*(?:(?:education|experience)(?: and (?:education|experience|qualifications?))?\s+requirements?|requirements?|qualifications?|skills(?: and experience)?|criteria)|"
                  r"who you are|what you(?:'|’)ll (?:need|bring)|about you|job overview|your profile|you will have)\s*:?\s*", re.I)
KEEP_TOGETHER = {"Project", "Excel", "Office", "Primavera", "Power", "Word", "Outlook", "Engineering", "Management", "Surveying",
                 "Kingdom", "States", "Arab", "East", "Council", "Institute", "Institution", "Chartered", "Saudi", "Building"}


def _sentences(p):
    out, start = [], 0
    for m in re.finditer(r"(?<=[a-z\)])\s+(?=([A-Z][a-z]+))", p):
        head = p[start:m.start()]
        if head.count("(") != head.count(")") or m.group(1) in KEEP_TOGETHER:
            continue
        out.append(head)
        start = m.end()
    out.append(p[start:])
    return out


EN = set("the and of to in with for or a an as on at be is are your you will have has must experience knowledge degree years skills ability working".split())
FOREIGN = set("de la el en y los las del con para por une des et le les du dans avec pour sur da do em com uma os ao nos experiência experiencia expérience conocimiento conhecimento años anos ans die der und mit für von bei das ein eine durch ist wir zu im du sie unsere deine het een voor met van il di per che della".split())
DANGLING = set("in the of and to with for a an or as on at by from including such e.g eg i.e ie like our your their within".split())


def _english(p):
    w = re.findall(r"[a-záéíóúàâçêõãñü]+", p.lower())
    if not w:
        return True
    return sum(x in FOREIGN for x in w) <= max(1, sum(x in EN for x in w))


def _shorten(p, width):
    """Cut a long line at a clause end if possible, never leaving a dangling word or an open bracket."""
    if len(p) <= width:
        return p
    cut = p[:width]
    for sep in (". ", "; ", ", ", " – ", " - ", " ("):
        k = cut.rfind(sep)
        if k > width * 0.55:
            cut = cut[:k]
            break
    else:
        cut = cut.rsplit(" ", 1)[0]
    words = cut.rstrip(",;:( ").split(" ")
    while len(words) > 4 and words[-1].lower().strip(".,") in DANGLING:
        words.pop()
    cut = " ".join(words).rstrip(",;:( ")
    if cut.count("(") > cut.count(")"):
        cut = cut[:cut.rfind("(")].rstrip(",;: ")
    return cut + "…"


def _tidy(p):
    """No dangling last word ("experience in the") and no half-open brackets."""
    end = p.endswith("…")
    body = p.rstrip("…").rstrip(" ,;:")
    words = body.split(" ")
    popped = False
    while len(words) > 4 and words[-1].lower().strip(".,") in DANGLING:
        words.pop(); popped = True
    body = " ".join(words).rstrip(" ,;:(")
    first_close, first_open = body.find(")"), body.find("(")
    if first_close != -1 and (first_open == -1 or first_close < first_open):
        body = body[first_close + 1:].lstrip(" ,;:")          # "PowerPoint) Proficiency in ..." -> "Proficiency in ..."
    if body.count("(") > body.count(")"):
        body += ")"
    return body + ("…" if end or popped else "")


def lines(text, limit=5, width=190):
    t = clean(text)
    t = re.sub(r"\b(e)\.g\.|\b(i)\.e\.", lambda m: (m.group(1) or m.group(2)) + ("g" if m.group(1) else "e") + "\u2024", t, flags=re.I)
    parts = re.split(r"\s*(?:•|·|●|▪|◦|•|\s-\s|\s–\s|;|\|\|\|\||(?<=[a-z0-9\)])\.\s+(?=[A-Z]))\s*", t)
    split = []
    for p in parts:  # text that lost its bullet marks: break long runs where a new capitalised sentence starts
        split.extend(_sentences(p) if len(p) > 300 else [p])
    parts = split
    cands, seen = [], set()
    for i, p in enumerate(parts):
        p = re.sub(r"^(?:[A-Z][A-Z'’&/ ]{2,}\s){2,}", "", p.strip(" .,:;-–'\"’"))  # drop an UPPER-CASE heading in front
        p = HEAD.sub("", p).strip(" .,:;-–")
        p = re.sub(r"[\"']?\s*[a-z-]+=\"[^\"]*\"?|[a-z-]+:[^;\"]*;|\"", " ", p)  # leftover html attributes / inline styles
        p = re.sub(r"\b(\w+) s\b(?= (?:degree|or|in)\b)", r"\1's", p)
        p = re.sub(r"^(?:[b-hj-zB-HJ-Z]\s|&\w*;?\s*)+(?=[a-z]|[A-Z][a-z])", "", p.strip())  # stray letter in front ("D restoration")
        lead = re.match(r"^.{0,90}?(?:looking for|need to have|you(?:'|’)ll need|you will need|you(?:'|’)ll bring|must have|we need)\s*:?\s+", p, re.I)
        if lead:
            p = p[lead.end():]
        p = re.sub(r"\s+", " ", p).strip(" .,:;-–")
        p = p.replace("\u2024", ".").replace("eg.", "e.g.").replace("ie.", "i.e.")
        if i == 0 and p[:1].islower():
            continue  # the text was cut mid-word before this point
        p = re.sub(r"(?:\s+[a-z]){1,2}$", "", p)  # a stray tag letter at the end ("... Skills: p")
        if not (25 <= len(p) <= 400) or not CUE.search(p) or NOISE.search(p) or not _english(p):
            continue
        strong = bool(STRONG.search(p))
        if DUTY.search(p) and not strong:
            continue
        p = re.sub(r"\s*\b(?:style|class|lang|align|border|width)\s*=.*$", "", p)        # attribute cut off at the end
        p = _tidy(_shorten(p, width))
        if len(p) < 25:
            continue
        key = re.sub(r"[^a-z]", "", p.lower())[:60]
        if key in seen:
            continue
        seen.add(key)
        cands.append((0 if strong else 1, i, p[0].upper() + p[1:]))
    best = sorted(cands)[:limit]
    return [p for _, _, p in sorted(best, key=lambda x: x[1])]


def drop_boilerplate(per_job, share=0.15, min_jobs=6):
    """Remove lines that repeat across many postings of one employer (company blurb, standard clauses)."""
    if len(per_job) < min_jobs:
        return per_job
    count = {}
    for ls in per_job.values():
        for k in {re.sub(r"[^a-z]", "", l.lower())[:60] for l in ls}:
            count[k] = count.get(k, 0) + 1
    lim = max(2, share * len(per_job))
    return {j: [l for l in ls if count[re.sub(r"[^a-z]", "", l.lower())[:60]] < lim] for j, ls in per_job.items()}
