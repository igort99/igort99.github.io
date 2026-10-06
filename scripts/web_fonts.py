#!/usr/bin/env python3
"""Build the self-hosted web fonts in static/fonts from the Ubuntu system fonts.

Body text is Carlito, code is DejaVu Sans Mono: what the theme's font stack
falls back to on Ubuntu. Shipping them makes every OS render the same.

Fonts are subset to Latin/Greek/punctuation/math and unhinted to keep them
small. Carlito is OFL with a Reserved Font Name, so the modified copy is
renamed to "Body Sans".

Needs: apt fonts-crosextra-carlito fonts-dejavu-core; pip fonttools brotli
Usage: python3 scripts/web_fonts.py
"""
from fontTools import subset
from fontTools.ttLib import TTFont

SRC = "/usr/share/fonts/truetype"
OUT = "static/fonts"
UNICODES = (
    "U+0000-024F,U+0300-036F,U+0370-03FF,U+2000-206F,U+2070-209F,"
    "U+20A0-20CF,U+2100-218F,U+2190-21FF,U+2200-22FF,U+25A0-25FF,U+FB00-FB06"
)

# source file -> (output name, renamed family or None to keep the name)
FONTS = {
    "crosextra/Carlito-Regular.ttf": ("body-sans-regular", "Body Sans"),
    "crosextra/Carlito-Italic.ttf": ("body-sans-italic", "Body Sans"),
    "crosextra/Carlito-Bold.ttf": ("body-sans-bold", "Body Sans"),
    "crosextra/Carlito-BoldItalic.ttf": ("body-sans-bolditalic", "Body Sans"),
    "dejavu/DejaVuSansMono.ttf": ("dejavu-sans-mono", None),
    "dejavu/DejaVuSansMono-Bold.ttf": ("dejavu-sans-mono-bold", None),
}


def rename(font, family):
    """Replace the original family name in every name record."""
    old = font["name"].getDebugName(1)
    for rec in font["name"].names:
        new = family.replace(" ", "") if rec.nameID == 6 else family  # PostScript name: no spaces
        rec.string = rec.toUnicode().replace(old, new)


def build(src, out, family):
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.hinting = False
    opts.flavor = "woff2"
    opts.drop_tables += ["FFTM"]
    font = TTFont(f"{SRC}/{src}")
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=subset.parse_unicodes(UNICODES))
    sub.subset(font)
    if family:
        rename(font, family)
    subset.save_font(font, f"{OUT}/{out}.woff2", opts)
    print(f"{OUT}/{out}.woff2")


if __name__ == "__main__":
    for src, (out, family) in FONTS.items():
        build(src, out, family)
