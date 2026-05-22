#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

DEVTO_USERNAME = "nimay_04"
PROFILE_URL = f"https://dev.to/{DEVTO_USERNAME}"
API_URL = f"https://dev.to/api/articles?username={DEVTO_USERNAME}&per_page=3"
FEED_URL = f"https://dev.to/feed/{DEVTO_USERNAME}"
README_PATH = Path(__file__).resolve().parents[1] / "README.md"
START_MARKER = "<!-- DEVTO-LATEST:START -->"
END_MARKER = "<!-- DEVTO-LATEST:END -->"
USER_AGENT = "GitNimay README updater"


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, application/rss+xml, application/xml;q=0.9, */*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def fetch_api_articles() -> list[dict[str, Any]]:
    return json.loads(fetch_url(API_URL))


def fetch_feed_articles() -> list[dict[str, Any]]:
    root = ET.fromstring(fetch_url(FEED_URL))
    channel = root.find("channel")
    if channel is None:
        return []

    articles: list[dict[str, Any]] = []
    for item in channel.findall("item")[:3]:
        articles.append(
            {
                "title": item.findtext("title") or "Untitled",
                "url": item.findtext("link") or PROFILE_URL,
                "published_at": item.findtext("pubDate") or "",
                "user": {"name": item.findtext("{http://purl.org/dc/elements/1.1/}creator") or "Nimesh Kulkarni"},
            }
        )
    return articles


def fetch_articles() -> list[dict[str, Any]]:
    api_articles = fetch_api_articles()
    feed_articles = fetch_feed_articles()
    if not feed_articles:
        return api_articles

    api_by_url = {article.get("url", ""): article for article in api_articles}
    merged: list[dict[str, Any]] = []

    for feed_article in feed_articles:
        url = feed_article.get("url", "")
        merged.append({**feed_article, **api_by_url.get(url, {})})

    return merged[:3]


def format_date(value: str | None) -> str:
    if not value:
        return ""
    if "," in value:
        return parsedate_to_datetime(value).strftime("%b %d, %Y")
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

    rows: list[str] = []
    for article in articles[:3]:
        title = clean_text(article.get("title", "Untitled"), 90)
        url = article.get("url", PROFILE_URL)
        cover = article.get("cover_image") or article.get("social_image") or ""
        published = format_date(article.get("published_at", article.get("published_timestamp")))
        user = article.get("user", {})
        author = clean_text(user.get("name", "Nimesh Kulkarni"), 40)
        avatar = user.get("profile_image") or ""

        media = (
            f'<a href="{url}"><img src="{cover}" alt="{title}" width="160"></a>'
            if cover
            else ""
        )
        meta = [author]
        if published:
            meta.append(published)

        rows.extend([
            "  <tr>",
            f'    <td width="180" valign="top">{media}</td>',
            f'    <td valign="middle"><a href="{url}"><strong>{title}</strong></a><br><sub>{" · ".join(meta)}</sub></td>',
            "  </tr>",
        ])

    return "\n".join([
        "<table>",
        *rows,
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
