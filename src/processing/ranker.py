"""Rule-based article ranking."""

from __future__ import annotations

from src.llm.schemas import Article
from src.processing.deduplicate import SOURCE_AUTHORITY

MAJOR_KEYWORDS = {
    "war": 1.8,
    "attack": 1.5,
    "missile": 1.5,
    "ceasefire": 1.4,
    "election": 1.5,
    "president": 1.1,
    "central bank": 1.4,
    "fed": 1.3,
    "sanction": 1.5,
    "disaster": 1.4,
    "earthquake": 1.5,
    "flood": 1.3,
    "technology": 1.1,
    "ai": 1.3,
    "chip": 1.2,
    "finance": 1.2,
    "market": 1.1,
    "court": 1.2,
    "climate": 1.2,
    "geopolitics": 1.4,
    "tariff": 1.3,
    "trade": 1.1,
    "战争": 1.8,
    "选举": 1.5,
    "央行": 1.4,
    "制裁": 1.5,
    "灾害": 1.4,
    "人工智能": 1.3,
    "金融": 1.2,
    "法院": 1.2,
    "气候": 1.2,
}


def rank_items(items: list[Article]) -> list[Article]:
    for item in items:
        item.importance_score_base = round(_score_item(item), 2)
    return sorted(items, key=lambda article: article.importance_score_base or 0, reverse=True)


def _score_item(item: Article) -> float:
    text = f"{item.title} {item.summary or ''} {item.raw_text or ''}".lower()
    source_score = SOURCE_AUTHORITY.get(item.source_name, 5) * 1.5
    duplicate_score = min(len(item.duplicate_sources), 5) * 2.0
    keyword_score = sum(weight for keyword, weight in MAJOR_KEYWORDS.items() if keyword in text)
    length_score = min(len(item.raw_text or "") / 3000, 1.0) * 4.0
    density_score = _information_density_score(item.raw_text or item.summary or "")
    image_score = 0.5 if item.image_url else 0.0

    return source_score + duplicate_score + keyword_score + length_score + density_score + image_score


def _information_density_score(text: str) -> float:
    if not text:
        return 0.0
    tokens = text.split()
    if not tokens:
        return 0.0
    unique_ratio = len(set(token.lower().strip(".,:;!?()[]{}\"'") for token in tokens)) / len(tokens)
    return min(unique_ratio * 3.0, 3.0)
