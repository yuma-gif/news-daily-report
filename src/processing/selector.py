"""Final candidate selection before LLM analysis."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from src.llm.schemas import Article

logger = logging.getLogger(__name__)

SOFT_NEWS_KEYWORDS = {
    "sport",
    "sports",
    "football",
    "soccer",
    "nba",
    "world cup",
    "celebrity",
    "singer",
    "music",
    "movie",
    "film",
    "restaurant",
    "travel",
    "fashion",
    "lifestyle",
    "娱乐",
    "体育",
    "足球",
    "篮球",
    "明星",
    "歌手",
    "电影",
    "餐厅",
    "旅游",
    "时尚",
    "生活方式",
    "世界杯",
    "游戏",
    "8点1氪",
    "氪星晚报",
    "早报",
    "晚报",
}

BRIEF_NEWS_KEYWORDS = {
    "8点1氪",
    "早报",
    "晚报",
    "塌房",
    "一吻",
    "搭子",
}

MAJOR_EVENT_KEYWORDS = {
    "war",
    "strike",
    "attack",
    "election",
    "sanction",
    "tariff",
    "central bank",
    "court",
    "disaster",
    "earthquake",
    "ai",
    "chip",
    "finance",
    "战争",
    "袭击",
    "选举",
    "制裁",
    "关税",
    "央行",
    "法院",
    "灾害",
    "地震",
    "人工智能",
    "芯片",
    "金融",
}


@dataclass(frozen=True)
class SelectionResult:
    articles: list[Article]
    domestic_shortage: bool


def select_final_articles(
    candidates: list[Article],
    total_items: int = 12,
    domestic_min: int = 4,
    china_related_max: int = 2,
) -> SelectionResult:
    sorted_candidates = sorted(
        candidates,
        key=lambda article: article.importance_score_base or 0,
        reverse=True,
    )
    unique_candidates = _dedupe_events(sorted_candidates)
    primary_candidates = [article for article in unique_candidates if not _is_soft_news(article)]
    fallback_candidates = [article for article in unique_candidates if _is_soft_news(article)]

    selected: list[Article] = []
    domestic_pool = _pool(primary_candidates, "domestic_china")
    china_related_pool = _pool(primary_candidates, "china_related_international")
    international_pool = _pool(primary_candidates, "international")

    _append_unique(selected, domestic_pool, domestic_min)
    domestic_shortage = len(_pool(selected, "domestic_china")) < domestic_min
    if domestic_shortage:
        logger.warning(
            "Domestic China candidates below target: selected=%s target=%s",
            len(_pool(selected, "domestic_china")),
            domestic_min,
        )

    _append_unique(selected, china_related_pool, china_related_max)
    _append_unique(selected, international_pool, total_items - len(selected))

    if len(selected) < total_items:
        remaining_primary = [
            article
            for article in primary_candidates
            if article.url not in {selected_article.url for selected_article in selected}
        ]
        _append_unique(selected, remaining_primary, total_items - len(selected))

    if len(selected) < total_items:
        _append_unique(selected, fallback_candidates, total_items - len(selected))

    return SelectionResult(
        articles=selected[: min(total_items, len(unique_candidates))],
        domestic_shortage=domestic_shortage,
    )


def _append_unique(selected: list[Article], pool: list[Article], limit: int) -> None:
    selected_urls = {article.url for article in selected}
    for article in pool:
        if len([candidate for candidate in selected if candidate in pool]) >= limit:
            break
        if article.url in selected_urls:
            continue
        selected.append(article)
        selected_urls.add(article.url)


def _pool(articles: list[Article], region: str) -> list[Article]:
    return [article for article in articles if _region(article) == region]


def _region(article: Article) -> str:
    if article.source_region:
        return article.source_region
    if article.category == "china":
        return "domestic_china"
    return "international"


def _dedupe_events(articles: list[Article]) -> list[Article]:
    deduped: list[Article] = []
    for article in articles:
        normalized_title = _normalize_title(article.title)
        if any(
            SequenceMatcher(None, normalized_title, _normalize_title(existing.title)).ratio() > 0.90
            for existing in deduped
        ):
            continue
        deduped.append(article)
    return deduped


def _is_soft_news(article: Article) -> bool:
    text = f"{article.title} {article.summary or ''} {article.raw_text or ''}".lower()
    if any(keyword in text for keyword in BRIEF_NEWS_KEYWORDS):
        return True
    has_soft_keyword = any(_contains_keyword(text, keyword) for keyword in SOFT_NEWS_KEYWORDS)
    has_major_keyword = any(_contains_keyword(text, keyword) for keyword in MAJOR_EVENT_KEYWORDS)
    return has_soft_keyword and not has_major_keyword


def _normalize_title(title: str) -> str:
    return " ".join(title.lower().strip().split())


def _contains_keyword(text: str, keyword: str) -> bool:
    if keyword.isascii():
        pattern = r"(?<![a-z0-9])" + re.escape(keyword.lower()) + r"(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return keyword in text
