
"""Automatically update GitHub journey and stats image URLs."""

import datetime as dt
import html
import re
from pathlib import Path
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)

README = Path("README.md")
START_DATE = dt.date(2024, 10, 2)

today = dt.datetime.now(dt.timezone.utc).date()
version = today.strftime("%Y%m%d")

content = README.read_text(encoding="utf-8")

# 1. Update GitHub journey
start = "<!-- PROFILE-DATES:START -->"
end = "<!-- PROFILE-DATES:END -->"

if content.count(start) != 1 or content.count(end) != 1:
    raise ValueError("PROFILE-DATES markers missing or duplicated")

dates = (
    f"**GitHub journey:** {START_DATE:%d/%m/%Y}"
    f" → {today:%d/%m/%Y} (updated daily, UTC)"
)

content = re.sub(
    re.escape(start) + r".*?" + re.escape(end),
    lambda _: f"{start}\n{dates}\n{end}",
    content,
    flags=re.DOTALL,
)

# 2. Refresh GitHub stats image URLs
domains = {
    "github-stats-extended.vercel.app",
    "streak-stats.demolab.com",
    "github-profile-summary-cards.vercel.app",
}

updated = 0

def refresh_image(match):
    global updated

    original = match.group(1)
    url = html.unescape(original)
    parts = urlsplit(url)

    if parts.hostname not in domains:
        return match.group(0)

    params = [
        (key, value)
        for key, value in parse_qsl(
            parts.query, keep_blank_values=True
        )
        if key != "v"
    ]

    params.append(("v", version))

    new_url = urlunsplit(
        parts._replace(query=urlencode(params))
    )

    updated += 1

    return f'src="{html.escape(new_url, quote=True)}"'

content = re.sub(
    r'src="([^"]+)"',
    refresh_image,
    content,
)

if updated < 4:
    raise ValueError(
        f"Expected 4 stats images, found {updated}"
    )

# 3. Save README
README.write_text(content, encoding="utf-8")

print(f"GitHub journey updated: {today}")
print(f"Stats images refreshed: {updated}")
print(f"Cache version: {version}")
