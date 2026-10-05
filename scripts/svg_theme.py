#!/usr/bin/env python3
"""Make dark-styled matplotlib SVGs follow the browser's light/dark setting.

Swaps the neutral greys for CSS variables and embeds a <style> that defines
them for dark (default) and light (prefers-color-scheme: light). Data colors
are left alone. Safe to re-run: already-processed files are skipped.

Usage: python3 scripts/svg_theme.py static/img/looped-cot/*.svg
"""
import re
import sys

MARKER = 'id="theme-vars"'

# dark color as rendered -> (variable, light-mode replacement)
PALETTE = {
    "#1a1a1a": ("--bg", "#ffffff"),     # figure background, marker edges
    "#ffffff": ("--title", "#111111"),  # bold titles
    "#c3c2b7": ("--ink", "#3d3d3a"),    # labels, ticks, annotations
    "#383835": ("--spine", "#c8c8c3"),  # axis lines
    "#2c2c2a": ("--grid", "#e4e4e0"),   # grid lines
}


def style_block():
    dark = " ".join(f"{v}: {d};" for d, (v, _) in PALETTE.items())
    light = " ".join(f"{v}: {l};" for v, l in PALETTE.values())
    return (
        f'<style {MARKER} type="text/css">'
        f"svg {{ {dark} }} "
        f"@media (prefers-color-scheme: light) {{ svg {{ {light} }} }} "
        # background-colored halo keeps labels readable where they overlap data
        "text { stroke: var(--bg); stroke-width: 3px; stroke-linejoin: round; paint-order: stroke; }"
        "</style>"
    )


def process(path):
    svg = open(path).read()
    if MARKER in svg:
        return False
    for dark, (var, _) in PALETTE.items():
        svg = re.sub(
            rf"((?:fill|stroke):\s*){re.escape(dark)}\b",
            rf"\1var({var})",
            svg,
            flags=re.IGNORECASE,
        )
    # put the variables right after the opening <svg ...> tag
    svg = re.sub(r"(<svg\b[^>]*>)", lambda m: m.group(1) + "\n " + style_block(), svg, count=1)
    open(path, "w").write(svg)
    return True


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(("themed  " if process(p) else "skipped ") + p)
