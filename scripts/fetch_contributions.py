#!/usr/bin/env python3
"""
fetch_contributions.py — pull your real 53-week contribution calendar
from GitHub's public HTML fragment (no GraphQL API, no personal access
token needed) and write data/contributions.json.

GitHub serves this at:
    https://github.com/users/<username>/contributions

It's the same fragment the profile page itself renders, so it's public
and stable, but it is an unofficial/undocumented endpoint — treat it as
best-effort, not an SLA.

Usage:
    python scripts/fetch_contributions.py [username]

If no username is given, it's read from the GITHUB_USERNAME env var,
falling back to the placeholder below.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "YOUR_USERNAME"
URL_TEMPLATE = "https://github.com/users/{username}/contributions"
OUTPUT_PATH = Path("data/contributions.json")


def fetch_html(username: str) -> str:
    url = URL_TEMPLATE.format(username=username)
    headers = {"User-Agent": "Mozilla/5.0 (profile-readme-bot)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    days = []
    # GitHub renders each day as a <td> with data-date / data-level,
    # or an <rect> with data-date/data-count/data-level depending on
    # markup version — handle both defensively.
    cells = soup.select("td.ContributionCalendar-day, rect.ContributionCalendar-day")
    for cell in cells:
        date_str = cell.get("data-date")
        if not date_str:
            continue
        level = cell.get("data-level")
        count_attr = cell.get("data-count")
        tooltip_id = cell.get("id")
        count = None
        if count_attr is not None:
            try:
                count = int(count_attr)
            except ValueError:
                count = None
        if count is None:
            # fall back to parsing the associated tooltip text, e.g.
            # "5 contributions on January 3rd."
            tooltip = None
            if tooltip_id:
                tooltip = soup.find(attrs={"for": tooltip_id})
            if tooltip and tooltip.text:
                text = tooltip.text.strip()
                first_word = text.split(" ")[0]
                if first_word.lower() == "no":
                    count = 0
                else:
                    try:
                        count = int(first_word)
                    except ValueError:
                        count = 0
            else:
                count = 0
        days.append({
            "date": date_str,
            "count": count,
            "level": int(level) if level is not None else 0,
        })
    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)

    # streaks
    longest = current = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    # current streak counts back from the most recent day
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        else:
            break

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly = defaultdict(int)
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[d["count"]] if False else None
        monthly[month_key] += d["count"]

    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly_totals": dict(sorted(monthly.items())),
    }


def main():
    username = (
        sys.argv[1] if len(sys.argv) > 1
        else os.environ.get("GITHUB_USERNAME", DEFAULT_USERNAME)
    )
    if username == DEFAULT_USERNAME:
        print(f"Warning: using placeholder username '{username}'. "
              f"Pass a real one: python scripts/fetch_contributions.py <username>")

    print(f"Fetching contributions for {username} ...")
    html = fetch_html(username)
    days = parse_days(html)
    if not days:
        print("Warning: no day cells parsed — GitHub's markup may have changed.")
    stats = compute_stats(days)

    payload = {
        "username": username,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(days)} days, {stats['total']} contributions)")


if __name__ == "__main__":
    main()
