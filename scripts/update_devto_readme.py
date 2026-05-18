#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

DEVTO_USERNAME = "nimay_04"
PROFILE_URL = f"https://dev.to/{DEVTO_USERNAME}"
API_URL = f"https://dev.to/api/articles?username={DEVTO_USERNAME}&per_page=3"
README_PATH = Path(__file__).resolve().parents[1] / "README.md"
START_MARKER = "<!-- DEVTO-LATEST:START -->"
END_MARKER = "<!-- DEVTO-LATEST:END -->"
USER_AGENT = "GitNimay README updater"


def fetch_articles() -> list[dict[str, Any]]:
    request = urllib.request.Request(API_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def format_date(value: str | None) -> str:
    if not value:
        return ""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%b %d, %Y")


def clean_text(value: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", value or "").strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def render_articles(articles: list[dict[str, Any]]) -> str:
    if not articles:
        return (
            '<p><a href="https://dev.to/nimay_04">View my writing on DEV</a></p>'
        )

    cells: list[str] = []
    for article in articles[:3]:
        title = clean_text(article.get("title", "Untitled"), 72)
        description = clean_text(article.get("description", ""), 140)
        url = article.get("url", PROFILE_URL)
        cover = article.get("cover_image") or article.get("social_image") or ""
        published = format_date(article.get("published_at", article.get("published_timestamp")))
        user = article.get("user", {})
        author = clean_text(user.get("name", "Nimesh Kulkarni"), 40)
        avatar = user.get("profile_image") or ""

        parts = [f'<a href="{url}"><img src="{cover}" alt="{title}" width="100%"></a>' if cover else ""]
        parts.append(f'<br><a href="{url}"><strong>{title}</strong></a>')
        if description:
            parts.append(f'<br><sub>{description}</sub>')
        meta = []
        if avatar:
            meta.append(f'<img src="{avatar}" alt="{author}" width="18" height="18">')
        meta.append(author)
        meta.append(published)
        parts.append(f'<br><sub>{" · ".join(meta)}</sub>')
        cells.append(f'<td width="33.33%" valign="top">{"".join(parts)}</td>')

    return "\n".join([
        "<table>",
        "  <tr>",
        *[f"    {cell}" for cell in cells],
        "  </tr>",
        "</table>",
        f'<p><a href="{PROFILE_URL}">View all on DEV</a></p>',
    ])


def update_readme(content: str, replacement: str) -> str:
    pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL,
    )
    block = f"{START_MARKER}\n{replacement}\n{END_MARKER}"
    if START_MARKER in content and END_MARKER in content:
        return pattern.sub(block, content, count=1)
    raise RuntimeError("README markers not found")


def main() -> None:
    articles = fetch_articles()
    readme = README_PATH.read_text(encoding="utf-8")
    updated = update_readme(readme, render_articles(articles))
    README_PATH.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
