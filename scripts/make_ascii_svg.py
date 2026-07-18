#!/usr/bin/env python3
"""
make_ascii_svg.py — convert source-prepped.png into avi-ascii.svg: a
monochrome ASCII portrait that types itself in, row by row, using SMIL
animation (no JavaScript, no looping — plays once and freezes).

Usage:
    python scripts/make_ascii_svg.py [input.png] [output.svg]
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Bright (sparse) -> dark (dense). Leading space clears the background
# to nothing, so a bright/white background prints as empty.
RAMP = " .:-=+*cs#%@"

COLS = 100
ROWS = 53

CHAR_W = 6.4      # px per column at the chosen font-size
CHAR_H = 11.0      # px per row
FONT_SIZE = 11
FILL_COLOR = "var(--ascii-fill, #9fb4c7)"   # single light-gray/blue fill
BG_COLOR = "transparent"

ROW_STAGGER = 0.045   # seconds between each row starting
ROW_DURATION = 0.35   # seconds for a row's wipe to complete


def image_to_grid(img: Image.Image, cols: int, rows: int) -> list[str]:
    """Downsample the grayscale image to a cols x rows character grid."""
    small = img.resize((cols, rows), Image.LANCZOS)
    arr = np.array(small, dtype=np.float32)
    # Normalize 0..1, 0 = black (dense glyph), 1 = white (space)
    norm = arr / 255.0
    lines = []
    ramp_len = len(RAMP) - 1
    for r in range(rows):
        line_chars = []
        for c in range(cols):
            brightness = norm[r, c]
            # invert: bright -> low density index (near space)
            idx = int(round((1.0 - brightness) * ramp_len))
            idx = max(0, min(ramp_len, idx))
            line_chars.append(RAMP[idx])
        lines.append("".join(line_chars))
    return lines


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(lines: list[str]) -> str:
    width = COLS * CHAR_W
    height = ROWS * CHAR_H + 20

    rows_svg = []
    for i, line in enumerate(lines):
        text_content = escape_xml(line) if line.strip() else " "
        row_width = len(line) * CHAR_W
        y = 10 + i * CHAR_H + FONT_SIZE * 0.8
        start_time = i * ROW_STAGGER

        clip_id = f"clip-row-{i}"

        rows_svg.append(f'''
    <clipPath id="{clip_id}">
      <rect x="0" y="{10 + i * CHAR_H}" width="0" height="{CHAR_H}">
        <animate attributeName="width" from="0" to="{row_width}"
                 begin="{start_time:.3f}s" dur="{ROW_DURATION}s"
                 fill="freeze" calcMode="spline"
                 keySplines="0.25 0.1 0.25 1" />
      </rect>
    </clipPath>
    <text x="0" y="{y:.1f}" font-family="'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
          font-size="{FONT_SIZE}" fill="{FILL_COLOR}" xml:space="preserve"
          clip-path="url(#{clip_id})">{text_content}</text>
    <rect class="cursor" x="0" y="{10 + i * CHAR_H}" width="2" height="{CHAR_H - 2}" fill="{FILL_COLOR}" opacity="0.85">
      <animate attributeName="x" from="0" to="{row_width}"
               begin="{start_time:.3f}s" dur="{ROW_DURATION}s"
               fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1" />
      <animate attributeName="opacity" from="0.85" to="0"
               begin="{start_time + ROW_DURATION:.3f}s" dur="0.15s" fill="freeze" />
    </rect>''')

    body = "\n".join(rows_svg)

    return f'''<svg viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ASCII portrait">
  <style>
    text {{ white-space: pre; }}
  </style>
  <rect width="100%" height="100%" fill="{BG_COLOR}" />
  <g>{body}
  </g>
</svg>
'''


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("source-prepped.png")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("profile-ascii.svg")

    if not input_path.exists():
        print(f"Error: {input_path} not found. Run prep_photo.py first.")
        sys.exit(1)

    img = Image.open(input_path).convert("L")
    lines = image_to_grid(img, COLS, ROWS)
    svg = build_svg(lines)
    output_path.write_text(svg, encoding="utf-8")
    print(f"Wrote {output_path} ({COLS}x{ROWS} chars)")


if __name__ == "__main__":
    main()
