"""Branded link-preview image (1200x630) for one job: discipline tag, job title, employer and location.
Shown by LinkedIn, WhatsApp, Facebook, X and Telegram when a job link is shared."""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
INK, MUTED, ACCENT, CHIP = (11, 29, 34), (61, 83, 89), (10, 112, 122), (227, 240, 241)
X0, X1, BOTTOM = 112, 1088, 548   # text area inside the card

_cache = {}


def _font(name, size):
    k = (name, size)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(os.path.join(ASSETS, "fonts", name), size)
    return _cache[k]


def _base():
    if "base" not in _cache:
        _cache["base"] = Image.open(os.path.join(ASSETS, "og-base.png")).convert("RGB")
    return _cache["base"]


def _wrap(draw, text, font, width, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
            continue
        if cur:
            lines.append(cur)
        cur = w
        if len(lines) == max_lines:
            break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    used = " ".join(lines)
    if len(used) < len(" ".join(words)):                      # did not fit: end the last line with …
        last = lines[-1]
        while last and draw.textlength(last + "…", font=font) > width:
            last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
        lines[-1] = last.rstrip(" ,–-") + "…"
    return lines


def render(job, path):
    img = _base().copy()
    d = ImageDraw.Draw(img)
    title = " ".join(str(job.get("title") or "").split())
    sub = " · ".join(x for x in (job.get("emp"), ", ".join(y for y in (job.get("city"), job.get("country")) if y)) if x)
    # title: biggest size that fits in 3 lines
    for size in (72, 64, 56, 50, 44):
        f = _font("Inter-Bold.otf", size)
        lines = _wrap(d, title, f, X1 - X0, 3)
        if not lines[-1].endswith("…") or size == 44:
            break
    lh = int(size * 1.12)
    fs = _font("Inter-Medium.otf", 30)
    sub_lines = _wrap(d, sub, fs, X1 - X0, 1)
    # lay out from the bottom up
    y_sub = BOTTOM - 36
    y_title = y_sub - 26 - lh * len(lines)
    chip = f"{job.get('disc') or 'Project controls'} role"
    fc = _font("Inter-Bold.otf", 26)
    cw = int(d.textlength(chip, font=fc)) + 40
    y_chip = y_title - 72
    d.rounded_rectangle([X0, y_chip, X0 + cw, y_chip + 50], radius=25, fill=CHIP)
    d.text((X0 + 20, y_chip + 9), chip, font=fc, fill=ACCENT)
    for i, line in enumerate(lines):
        d.text((X0 - 3, y_title + i * lh), line, font=f, fill=INK)
    d.text((X0, y_sub), sub_lines[0] if sub_lines else "", font=fs, fill=MUTED)
    img = img.quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    img.save(path, optimize=True)
