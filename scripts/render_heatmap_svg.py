#!/usr/bin/env python3
"""
render_heatmap_svg.py — render data/contributions.json as the classic
53-week x 7-day calendar of rounded boxes, with a diagonal line-after-line
reveal (CSS keyframes, plays once on load, then freezes).

Usage:
    python scripts/render_heatmap_svg.py [input.json] [output.svg]
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
# none -> brightest (level 5 is a neon top end, beyond GitHub's own scale,
# used here only for exceptionally high-count days if you want to extend it)

BOX = 11
GAP = 3
CELL = BOX + GAP
LEFT_PAD = 30      # room for weekday labels
TOP_PAD = 20        # room for month labels
LEGEND_H = 30
STATS_H = 24

STAGGER_PER_DIAGONAL = 0.02   # seconds between diagonals (week+day index sum)
BOX_DURATION = 0.28


def load_data(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def to_weeks(days: list[dict]) -> list[list[dict | None]]:
    """Bucket the flat day list into GitHub-style weeks (columns), Sun-Sat rows."""
    if not days:
        return []
    weeks: list[list[dict | None]] = []
    current_week: list[dict | None] = [None] * 7
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        weekday = (dt.weekday() + 1) % 7  # convert Mon=0..Sun=6 -> Sun=0..Sat=6
        if weekday == 0 and any(current_week):
            weeks.append(current_week)
            current_week = [None] * 7
        current_week[weekday] = d
    if any(current_week):
        weeks.append(current_week)
    return weeks[-53:]  # keep the last 53 weeks


def month_labels(weeks: list[list[dict | None]]) -> list[tuple[int, str]]:
    labels = []
    last_month = None
    for w_idx, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            month = day["date"][:7]
            if month != last_month:
                labels.append((w_idx, datetime.strptime(day["date"], "%Y-%m-%d").strftime("%b")))
                last_month = month
            break
    return labels


def color_for_level(level: int) -> str:
    return PALETTE[max(0, min(level, len(PALETTE) - 1))]


def build_svg(data: dict) -> str:
    days = data.get("days", [])
    stats = data.get("stats", {})
    weeks = to_weeks(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * CELL + 10
    height = TOP_PAD + 7 * CELL + LEGEND_H + STATS_H

    boxes = []
    for w_idx, week in enumerate(weeks):
        for d_idx, day in enumerate(week):
            if day is None:
                continue
            x = LEFT_PAD + w_idx * CELL
            y = TOP_PAD + d_idx * CELL
            color = color_for_level(day.get("level", 0))
            diagonal = w_idx + d_idx
            delay = diagonal * STAGGER_PER_DIAGONAL
            title = f"{day['count']} contributions on {day['date']}"
            boxes.append(f'''
    <rect class="cell" x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2" fill="{color}"
          style="animation-delay:{delay:.3f}s">
      <title>{title}</title>
    </rect>''')

    labels = month_labels(weeks)
    label_svg = "\n".join(
        f'    <text x="{LEFT_PAD + w_idx * CELL}" y="{TOP_PAD - 6}" '
        f'font-size="10" fill="#8b949e" font-family="sans-serif">{name}</text>'
        for w_idx, name in labels
    )

    legend_y = TOP_PAD + 7 * CELL + 18
    legend_swatches = "".join(
        f'<rect x="{width - 150 + i * (BOX + 4)}" y="{legend_y - 9}" width="{BOX}" height="{BOX}" '
        f'rx="2" fill="{color_for_level(i)}" />'
        for i in range(len(PALETTE))
    )

    total = stats.get("total", 0)
    footer = f"{total:,} contributions in the last year"

    return f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Contribution heatmap">
  <style>
    .cell {{
      opacity: 0;
      transform-origin: center;
      animation: reveal {BOX_DURATION}s ease-out forwards;
    }}
    @keyframes reveal {{
      from {{ opacity: 0; transform: translateY(-6px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
  </style>
  <rect width="100%" height="100%" fill="transparent" />
{label_svg}
  <g>{"".join(boxes)}
  </g>
  <text x="{LEFT_PAD}" y="{legend_y}" font-size="10" fill="#8b949e" font-family="sans-serif">Less</text>
  {legend_swatches}
  <text x="{width - 20}" y="{legend_y}" font-size="10" fill="#8b949e" font-family="sans-serif" text-anchor="end">More</text>
  <text x="{LEFT_PAD}" y="{height - 6}" font-size="12" fill="#c9d1d9" font-family="sans-serif">{footer}</text>
</svg>
'''


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/contributions.json")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("contrib-heatmap.svg")

    if not input_path.exists():
        print(f"Error: {input_path} not found. Run fetch_contributions.py first.")
        sys.exit(1)

    data = load_data(input_path)
    svg = build_svg(data)
    output_path.write_text(svg, encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
