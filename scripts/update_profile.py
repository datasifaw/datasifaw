"""Update GitHub profile lifetime and list all public, non-fork repositories."""
import datetime as dt
import html
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "datasifaw"
README = Path("README.md")
TOKEN = os.environ.get("GH_TOKEN", "")


def api(path):
    req = Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "datasifaw-profile-readme",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urlopen(req, timeout=25) as response:
        return json.load(response)


def replace_section(content, marker, value):
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    if content.count(start) != 1 or content.count(end) != 1:
        raise ValueError(f"Missing or duplicated README markers: {marker}")
    before, remainder = content.split(start, 1)
    _, after = remainder.split(end, 1)
    return before + start + "\n" + value + "\n" + end + after


profile = api(f"/users/{USERNAME}")
repos = []
page = 1
while True:
    batch = api(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner&sort=updated")
    if not batch:
        break
    repos.extend(batch)
    if len(batch) < 100:
        break
    page += 1

# Exclude the special README repository and forked projects.
repos = [r for r in repos if not r.get("fork") and r["name"].lower() != USERNAME.lower()]
repos.sort(key=lambda r: r["name"].casefold())

rows = ["| Project | Description | Language |", "| --- | --- | --- |"]
for repo in repos:
    name = html.escape(repo["name"], quote=False).replace("|", "\\|")
    description = html.escape(repo.get("description") or "—", quote=False).replace("|", "\\|").replace("\n", " ")
    language = html.escape(repo.get("language") or "—", quote=False).replace("|", "\\|")
    url = repo["html_url"]
    rows.append(f"| [{name}]({url}) | {description} | {language} |")
rows.append(f"\n**{len(repos)} public projects** (excluding forks and this profile repository).")

start_date = dt.date.fromisoformat(profile["created_at"][:10])
today = dt.datetime.now(dt.timezone.utc).date()
dates = f"**GitHub journey:** {start_date:%d/%m/%Y} → {today:%d/%m/%Y} (updated daily, UTC)"

content = README.read_text(encoding="utf-8")
content = replace_section(content, "PROFILE-DATES", dates)
content = replace_section(content, "ALL-PROJECTS", "\n".join(rows))
README.write_text(content, encoding="utf-8")
print(f"Updated profile from {start_date} to {today}: {len(repos)} projects")
