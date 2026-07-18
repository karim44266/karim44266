#!/usr/bin/env python3
"""
make_info_card.py — hand-author a neofetch-style SVG panel: a title bar,
then colored key/value rows. Each line fades + slides in on a short
stagger. Set STATIC=1 to emit a frozen final frame (for Quick Look /
local previews where SMIL doesn't animate).

Usage:
    python scripts/make_info_card.py [output.svg]
    STATIC=1 python scripts/make_info_card.py
"""

import os
import sys
from pathlib import Path

# ---- Edit this block with your own details ----------------------------
TITLE = "karim@github"
ROWS = [
    ("Now", "Big Data student, ISIMS Sfax (2026)"),
    ("Prev", "Full-stack dev + data pipelines"),
    ("Stack", "Python · TypeScript · React · NestJS · Docker"),
    ("Highlights", "EMM E-commerce Platform · TN Job Market Pipeline"),
]
ACCENT = "#39d353"      # key color (GitHub green)
VALUE_COLOR = "#c9d1d9"
TITLE_COLOR = "#e6edf3"
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
# -------------------------------------------------------------------------

WIDTH = 490
ROW_HEIGHT = 34
PADDING_TOP = 56
PADDING_X = 24
FONT_FAMILY = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

LINE_STAGGER = 0.25   # seconds between each row's fade-in start
LINE_DURATION = 0.45  # seconds for a row to fully fade/slide in


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(static: bool) -> str:
    height = PADDING_TOP + ROW_HEIGHT * len(ROWS) + 24

    rows_svg = []
    for i, (key, value) in enumerate(ROWS):
        y = PADDING_TOP + i * ROW_HEIGHT
        start = i * LINE_STAGGER

        if static:
            opacity_attr = 'opacity="1"'
            transform_attr = 'transform="translate(0,0)"'
            anims = ""
        else:
            opacity_attr = 'opacity="0"'
            transform_attr = ""
            anims = f'''
        <animate attributeName="opacity" from="0" to="1"
                 begin="{start:.3f}s" dur="{LINE_DURATION}s" fill="freeze" />
        <animateTransform attributeName="transform" type="translate"
                 from="-12,0" to="0,0" begin="{start:.3f}s"
                 dur="{LINE_DURATION}s" fill="freeze"
                 calcMode="spline" keySplines="0.25 0.1 0.25 1" />'''

        rows_svg.append(f'''
    <g {opacity_attr} {transform_attr}>{anims}
      <text x="{PADDING_X}" y="{y}" font-family="{FONT_FAMILY}" font-size="14"
            font-weight="600" fill="{ACCENT}">{escape_xml(key)}</text>
      <text x="{PADDING_X + 120}" y="{y}" font-family="{FONT_FAMILY}" font-size="13"
            fill="{VALUE_COLOR}">{escape_xml(value)}</text>
    </g>''')

    body = "\n".join(rows_svg)

    title_bar = f'''
  <rect x="0" y="0" width="{WIDTH}" height="34" rx="8" fill="{BORDER_COLOR}" />
  <circle cx="18" cy="17" r="5" fill="#ff5f56" />
  <circle cx="36" cy="17" r="5" fill="#ffbd2e" />
  <circle cx="54" cy="17" r="5" fill="#27c93f" />
  <text x="{WIDTH / 2:.0f}" y="21" text-anchor="middle" font-family="{FONT_FAMILY}"
        font-size="12" fill="{TITLE_COLOR}">{escape_xml(TITLE)}</text>'''

    return f'''<svg viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Info card">
  <rect x="0" y="0" width="{WIDTH}" height="{height}" rx="10" fill="{BG_COLOR}"
        stroke="{BORDER_COLOR}" stroke-width="1" />
  {title_bar}
  <g>{body}
  </g>
</svg>
'''


def main():
    static = os.environ.get("STATIC") == "1"
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("info-card.svg")
    svg = build_svg(static)
    output_path.write_text(svg, encoding="utf-8")
    mode = "static frame" if static else "animated"
    print(f"Wrote {output_path} ({mode})")


if __name__ == "__main__":
    main()
