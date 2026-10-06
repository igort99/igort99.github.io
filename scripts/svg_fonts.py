#!/usr/bin/env python3
"""Embed DejaVu Sans into matplotlib SVGs so labels look the same on every OS.

Figures load via <img>, which can't fetch the site's web fonts, so each SVG
gets its own @font-face with a woff2 data URI, subset to just the characters
and faces (regular / bold / oblique) that file uses. Re-running replaces the
embedded fonts, so run it again after regenerating a figure.

Needs: apt fonts-dejavu-core; pip fonttools brotli
Usage: python3 scripts/svg_fonts.py static/img/looped-cot/*.svg
"""
import base64
import html
import io
import re
import sys

from fontTools import subset
from fontTools.ttLib import TTFont

SRC = "/usr/share/fonts/truetype/dejavu"
MARKER = 'id="embedded-fonts"'

# face file -> (@font-face weight, style)
FACES = {
    "DejaVuSans.ttf": ("400", "normal"),
    "DejaVuSans-Bold.ttf": ("700", "normal"),
    "DejaVuSans-Oblique.ttf": ("400", "italic"),
    "DejaVuSans-BoldOblique.ttf": ("700", "italic"),
}


def face_of(style):
    bold = re.search(r"font-weight:\s*(bold|[6-9]00)", style) is not None
    italic = re.search(r"font-style:\s*(italic|oblique)", style) is not None
    return {
        (False, False): "DejaVuSans.ttf",
        (True, False): "DejaVuSans-Bold.ttf",
        (False, True): "DejaVuSans-Oblique.ttf",
        (True, True): "DejaVuSans-BoldOblique.ttf",
    }[(bold, italic)]


def woff2_subset(face, chars):
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.hinting = False
    opts.flavor = "woff2"
    opts.drop_tables += ["FFTM"]
    font = TTFont(f"{SRC}/{face}")
    sub = subset.Subsetter(opts)
    sub.populate(text=chars)
    sub.subset(font)
    buf = io.BytesIO()
    subset.save_font(font, buf, opts)
    return base64.b64encode(buf.getvalue()).decode()


def process(path):
    svg = open(path).read()
    svg = re.sub(rf"\s*<style {MARKER}.*?</style>", "", svg, flags=re.DOTALL)

    chars = {}  # face -> characters drawn in it
    for attrs, body in re.findall(r"<text\b([^>]*)>(.*?)</text>", svg, flags=re.DOTALL):
        style = re.search(r'style="([^"]*)"', attrs)
        face = face_of(style.group(1) if style else "")
        chars[face] = chars.get(face, "") + html.unescape(re.sub(r"<[^>]+>", "", body))
    if not chars:
        return False

    rules = []
    for face, text in sorted(chars.items()):
        weight, style = FACES[face]
        data = woff2_subset(face, "".join(sorted(set(text))))
        rules.append(
            f"@font-face {{ font-family: 'DejaVu Sans'; font-weight: {weight}; "
            f"font-style: {style}; src: url(data:font/woff2;base64,{data}) format('woff2'); }}"
        )
    block = f'<style {MARKER} type="text/css">' + " ".join(rules) + "</style>"
    svg = re.sub(r"(<svg\b[^>]*>)", lambda m: m.group(1) + "\n " + block, svg, count=1)
    open(path, "w").write(svg)
    return True


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(("embedded " if process(p) else "skipped  ") + p)
