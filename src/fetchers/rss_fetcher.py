"""RSS fetching utilities."""

from __future__ import annotations

import logging
from calendar import timegm
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import feedparser
import yaml
from bs4 import BeautifulSoup

from src.config import Settings
from src.llm.schemas import Article

logger = logging.getLogger(__name__)


def load_rss_sources(sources_path: Path | str = "config/sources.yaml") -> list[dict[str, Any]]:
    with Path(sources_path).open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data.get("rss_sources", [])


def fetch_rss_sources(
    settings: Settings,
    sources_path: Path | str = "config/sources.yaml",
) -> list[Article]:
    sources = load_rss_sources(sources_path)
    cutoff = datetime.now(UTC) - timedelta(hours=settings.news_lookback_hours)
    articles: list[Article] = []

    for source in sources:
        source_name = source.get("name", "Unknown Source")
        source_url = source.get("url")
        if not source.get("enabled", True):
            logger.info("Skipping disabled RSS source: %s", source_name)
            continue

        category_hint = source.get("category_hint") or source.get("region")

        if not source_url:
            logger.warning("Skipping RSS source without url: %s", source_name)
            logger.info("Fetched 0 articles from %s", source_name)
            continue

        try:
            feed = feedparser.parse(source_url)
            if getattr(feed, "bozo", False):
                logger.warning("RSS parse warning for %s: %s", source_name, feed.bozo_exception)

            source_count = 0
            for entry in feed.entries:
                article = _entry_to_article(entry, source, category_hint)
                if _should_keep_article(article, cutoff):
                    articles.append(article)
                    source_count += 1
            logger.info("Fetched %s articles from %s", source_count, source_name)
        except Exception as exc:
            logger.warning("Failed to fetch RSS source %s: %s", source_name, exc)
            logger.info("Fetched 0 articles from %s", source_name)

    return articles


def audit_rss_sources(
    settings: Settings,
    sources_path: Path | str = "config/sources.yaml",
) -> list[dict[str, Any]]:
    sources = load_rss_sources(sources_path)
    cutoff = datetime.now(UTC) - timedelta(hours=settings.news_lookback_hours)
    results: list[dict[str, Any]] = []

    for source in sources:
        result = {
            "name": source.get("name", "Unknown Source"),
            "region": source.get("region"),
            "language": source.get("language"),
            "enabled": bool(source.get("enabled", True)),
            "fetched_count": 0,
            "warning": None,
            "titles": [],
        }
        source_url = source.get("url")

        if not result["enabled"]:
            result["warning"] = "disabled"
            results.append(result)
            continue
        if not source_url:
            result["warning"] = "missing url"
            results.append(result)
            continue

        try:
            feed = feedparser.parse(source_url)
            if getattr(feed, "bozo", False):
                result["warning"] = str(feed.bozo_exception)

            for entry in feed.entries:
                article = _entry_to_article(
                    entry,
                    source,
                    source.get("category_hint") or source.get("region"),
                )
                if _should_keep_article(article, cutoff):
                    result["fetched_count"] += 1
                    if len(result["titles"]) < 3 and article.title:
                        result["titles"].append(article.title)
        except Exception as exc:
            result["warning"] = str(exc)

        results.append(result)

    return results


def _entry_to_article(
    entry: Any,
    source: dict[str, Any],
    category_hint: str | None,
) -> Article:
    published_at = _extract_published_at(entry)
    summary = _clean_html(_first_present(entry, ["summary", "description"]))
    raw_text = _clean_html(_first_present(entry, ["content", "summary_detail"]))

    return Article(
        title=_first_present(entry, ["title"]) or "",
        url=_first_present(entry, ["link", "id"]) or "",
        source_name=source.get("name", "Unknown Source"),
        source_region=source.get("region"),
        source_language=source.get("language"),
        source_weight=float(source.get("weight", 1.0) or 1.0),
        published_at=published_at,
        summary=summary,
        category_hint=_extract_category_hint(entry, category_hint),
        image_url=_extract_image_url(entry),
        raw_text=raw_text,
        duplicate_sources=[],
        importance_score_base=None,
        missing_published_at=published_at is None,
    )


def _should_keep_article(article: Article, cutoff: datetime) -> bool:
    if article.missing_published_at:
        return True
    if article.published_at is None:
        return True

    try:
        published_at = datetime.fromisoformat(article.published_at)
    except ValueError:
        return True

    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=UTC)
    return published_at >= cutoff


def _extract_published_at(entry: Any) -> str | None:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        value = getattr(entry, key, None)
        if value:
            return datetime.fromtimestamp(timegm(value), tz=UTC).isoformat()

    for key in ("published", "updated", "created"):
        value = getattr(entry, key, None)
        if value:
            parsed = feedparser._parse_date(value)
            if parsed:
                return datetime.fromtimestamp(timegm(parsed), tz=UTC).isoformat()

    return None


def _extract_image_url(entry: Any) -> str | None:
    for item in getattr(entry, "media_content", []) or []:
        url = item.get("url")
        if url:
            return url

    for item in getattr(entry, "media_thumbnail", []) or []:
        url = item.get("url")
        if url:
            return url

    for item in getattr(entry, "enclosures", []) or []:
        url = item.get("href") or item.get("url")
        mime_type = item.get("type", "")
        if url and (not mime_type or mime_type.startswith("image/")):
            return url

    return None


def _extract_category_hint(entry: Any, source_category_hint: str | None) -> str | None:
    hints = [source_category_hint] if source_category_hint else []
    tags = getattr(entry, "tags", None)
    if tags:
        terms = [tag.get("term") for tag in tags if tag.get("term")]
        if terms:
            hints.extend(terms[:3])
    return ", ".join(dict.fromkeys(hints)) if hints else None


def _first_present(entry: Any, keys: list[str]) -> str | None:
    for key in keys:
        value = getattr(entry, key, None)
        if isinstance(value, list) and value:
            first = value[0]
            if isinstance(first, dict):
                value = first.get("value")
        elif isinstance(value, dict):
            value = value.get("value")

        if value:
            return str(value)
    return None


def _clean_html(value: str | None) -> str | None:
    if not value:
        return None
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    return text or None
