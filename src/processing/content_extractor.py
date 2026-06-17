"""Article body extraction utilities."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import trafilatura
from bs4 import BeautifulSoup

from src.llm.schemas import Article

logger = logging.getLogger(__name__)

MAX_RAW_TEXT_LENGTH = 3000
REQUEST_TIMEOUT_SECONDS = 6
USER_AGENT = "NewsMVP/0.1 (+https://local.news.mvp)"
MAX_WORKERS = 10


def enrich_articles_with_raw_text(articles: list[Article]) -> list[Article]:
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_index = {
            executor.submit(extract_article_text, article): index
            for index, article in enumerate(articles)
        }
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                articles[index].raw_text = future.result()
            except Exception as exc:
                logger.warning("Body extraction failed for %s: %s", articles[index].url, exc)
                articles[index].raw_text = _truncate(articles[index].summary)
    return articles


def extract_article_text(article: Article) -> str | None:
    html = _fetch_html(article.url)
    text = _extract_with_trafilatura(html)
    if not text:
        text = _extract_with_beautifulsoup(html)
    if not text:
        text = article.summary
    return _truncate(text)


def _fetch_html(url: str) -> str | None:
    if not url:
        return None

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.text
    except Exception as exc:
        logger.warning("Article HTML fetch failed for %s: %s", url, exc)
        return None


def _extract_with_trafilatura(html: str | None) -> str | None:
    if not html:
        return None

    try:
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )
        return _normalize_text(extracted)
    except Exception as exc:
        logger.warning("Trafilatura extraction failed: %s", exc)
        return None


def _extract_with_beautifulsoup(html: str | None) -> str | None:
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    candidates = soup.select("article p") or soup.select("main p") or soup.select("p")
    text = " ".join(node.get_text(" ", strip=True) for node in candidates)
    return _normalize_text(text)


def _normalize_text(text: str | None) -> str | None:
    if not text:
        return None
    normalized = " ".join(text.split())
    return normalized or None


def _truncate(text: str | None) -> str | None:
    if not text:
        return None
    return text[:MAX_RAW_TEXT_LENGTH]
