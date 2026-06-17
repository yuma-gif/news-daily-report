"""Article deduplication."""

from __future__ import annotations

from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from src.llm.schemas import Article

TITLE_SIMILARITY_THRESHOLD = 0.82

SOURCE_AUTHORITY = {
    "Reuters World": 10,
    "Reuters China": 10,
    "AP News": 9,
    "BBC World": 9,
    "BBC Asia": 9,
    "The Guardian World": 8,
    "Al Jazeera": 8,
    "Nikkei Asia": 8,
    "South China Morning Post": 7,
    "Xinhua": 7,
    "CGTN": 6,
}


def deduplicate_items(items: list[Article]) -> list[Article]:
    url_deduped: list[Article] = []
    by_url: dict[str, Article] = {}

    for item in items:
        normalized_url = _normalize_url(item.url)
        if normalized_url and normalized_url in by_url:
            winner = _merge_duplicates(by_url[normalized_url], item)
            by_url[normalized_url] = winner
        else:
            by_url[normalized_url] = item

    url_deduped = list(by_url.values())
    title_deduped: list[Article] = []

    for item in url_deduped:
        duplicate_index = _find_title_duplicate_index(item, title_deduped)
        if duplicate_index is None:
            title_deduped.append(item)
            continue

        title_deduped[duplicate_index] = _merge_duplicates(
            title_deduped[duplicate_index],
            item,
        )

    return title_deduped


def _find_title_duplicate_index(item: Article, candidates: list[Article]) -> int | None:
    title = _normalize_title(item.title)
    if not title:
        return None

    for index, candidate in enumerate(candidates):
        candidate_title = _normalize_title(candidate.title)
        if not candidate_title:
            continue
        similarity = SequenceMatcher(None, title, candidate_title).ratio()
        if similarity > TITLE_SIMILARITY_THRESHOLD:
            return index
    return None


def _merge_duplicates(existing: Article, incoming: Article) -> Article:
    existing_quality = _article_quality(existing)
    incoming_quality = _article_quality(incoming)
    winner, loser = (
        (incoming, existing) if incoming_quality > existing_quality else (existing, incoming)
    )

    merged_sources = list(dict.fromkeys(
        winner.duplicate_sources
        + [loser.source_name]
        + loser.duplicate_sources
    ))
    winner.duplicate_sources = [
        source for source in merged_sources if source and source != winner.source_name
    ]
    return winner


def _article_quality(article: Article) -> tuple[int, int, int]:
    return (
        SOURCE_AUTHORITY.get(article.source_name, 5),
        len(article.raw_text or ""),
        len(article.summary or ""),
    )


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            urlencode(filtered_query),
            "",
        )
    )


def _normalize_title(title: str) -> str:
    return " ".join(title.lower().strip().split())
