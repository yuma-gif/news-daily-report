"""Rule-based article classification."""

from __future__ import annotations

from src.llm.schemas import Article

CHINA_KEYWORDS = {
    "china",
    "chinese",
    "beijing",
    "xi",
    "hong kong",
    "taiwan",
    "mainland",
    "prc",
    "中国",
    "北京",
    "香港",
    "台湾",
    "大陆",
    "习近平",
}


def classify_items(items: list[Article]) -> list[Article]:
    for item in items:
        score = _china_score(item)
        if score >= 2:
            item.category = "china"
            item.low_confidence = False
        else:
            item.category = "international"
            item.low_confidence = score == 1
    return items


def _china_score(item: Article) -> int:
    score = 0
    category_hint = (item.category_hint or "").lower()
    title = (item.title or "").lower()
    body = (item.raw_text or item.summary or "").lower()

    if "china" in category_hint or "中国" in category_hint:
        score += 1
    if _contains_china_keyword(title):
        score += 2
    if _contains_china_keyword(body):
        score += 1
    return score


def _contains_china_keyword(text: str) -> bool:
    return any(keyword in text for keyword in CHINA_KEYWORDS)
