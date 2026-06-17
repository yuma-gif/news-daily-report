"""Pydantic schemas for news processing and LLM structured outputs."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Article(BaseModel):
    title: str
    url: str
    source_name: str
    source_region: str | None = None
    source_language: str | None = None
    source_weight: float | None = None
    published_at: str | None = None
    summary: str | None = None
    category_hint: str | None = None
    image_url: str | None = None
    raw_text: str | None = None
    duplicate_sources: list[str] = Field(default_factory=list)
    importance_score_base: float | None = None
    missing_published_at: bool = False
    category: str | None = None
    low_confidence: bool = False


class NewsItemSummary(BaseModel):
    title: str
    summary: str
    region: str
    importance_score: float


class SourceOutput(BaseModel):
    source_name: str
    title: str
    url: str


class ImageOutput(BaseModel):
    image_url: str
    caption: str
    source_name: str
    source_url: str


LIMITED_SOURCE_UNCERTAINTY = "该事件目前仅有一个来源，信息完整性和后续进展仍需继续确认。"


def normalize_report_payload(payload: dict[str, Any]) -> dict[str, Any]:
    items = payload.get("items")
    if not isinstance(items, list):
        return payload

    for item in items:
        if not isinstance(item, dict):
            continue
        item["importance_score"] = _normalize_importance_score(
            item.get("importance_score"),
            item.get("rank"),
        )
        _ensure_limited_source_uncertainty(item)

    payload["total_items"] = len(items)
    payload["china_items"] = sum(
        1 for item in items if isinstance(item, dict) and item.get("category") == "china"
    )
    payload["international_items"] = sum(
        1
        for item in items
        if isinstance(item, dict) and item.get("category") == "international"
    )
    return payload


def _normalize_importance_score(value: Any, rank: Any) -> int:
    if value is None:
        score = _score_from_rank(rank)
    elif isinstance(value, str):
        try:
            score = round(float(value.strip()))
        except ValueError:
            score = _score_from_rank(rank)
    elif isinstance(value, (int, float)):
        score = round(value)
    else:
        score = _score_from_rank(rank)
    return max(0, min(100, int(score)))


def _score_from_rank(rank: Any) -> int:
    try:
        rank_value = int(rank)
    except (TypeError, ValueError):
        rank_value = 12
    return max(50, 85 - max(rank_value - 1, 0) * 3)


def _ensure_limited_source_uncertainty(item: dict[str, Any]) -> None:
    sources = item.get("sources")
    if not isinstance(sources, list) or len(sources) != 1:
        return

    uncertainties = item.get("uncertainties")
    if not isinstance(uncertainties, list):
        uncertainties = []
        item["uncertainties"] = uncertainties

    uncertainty_text = " ".join(str(value) for value in uncertainties)
    normalized = uncertainty_text.lower()
    has_limited_source_note = any(
        phrase in uncertainty_text
        for phrase in ("来源较少", "单一来源", "需要后续确认")
    ) or any(
        phrase in normalized
        for phrase in ("limited source", "limited sources")
    )
    if not has_limited_source_note:
        uncertainties.append(LIMITED_SOURCE_UNCERTAINTY)


class NewsItemOutput(BaseModel):
    rank: int
    title: str
    category: Literal["china", "international"]
    importance_score: int = Field(ge=0, le=100)
    summary: str
    detailed_report: str
    positive_impacts: list[str]
    negative_impacts: list[str]
    risks: list[str]
    uncertainties: list[str]
    lessons: list[str]
    sources: list[SourceOutput] = Field(min_length=1)
    images: list[ImageOutput] = Field(default_factory=list, max_length=3)

    @field_validator(
        "summary",
        "detailed_report",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("field must not be empty")
        return value.strip()

    @model_validator(mode="after")
    def require_low_source_uncertainty(self) -> "NewsItemOutput":
        if len(self.sources) == 1:
            uncertainty_text = " ".join(self.uncertainties)
            normalized = uncertainty_text.lower()
            has_limited_source_note = any(
                phrase in uncertainty_text
                for phrase in ("来源较少", "单一来源", "需要后续确认")
            ) or any(
                phrase in normalized
                for phrase in ("limited source", "limited sources")
            )
            if not has_limited_source_note:
                self.uncertainties.append(LIMITED_SOURCE_UNCERTAINTY)
        return self


class NewsReportOutput(BaseModel):
    generated_at: str
    time_range_start: str
    time_range_end: str
    total_items: int
    china_items: int
    international_items: int
    items: list[NewsItemOutput]

    @model_validator(mode="after")
    def validate_counts(self) -> "NewsReportOutput":
        if self.total_items != len(self.items):
            raise ValueError("total_items must equal len(items)")
        china_count = sum(item.category == "china" for item in self.items)
        international_count = sum(item.category == "international" for item in self.items)
        if self.china_items != china_count:
            raise ValueError("china_items does not match item categories")
        if self.international_items != international_count:
            raise ValueError("international_items does not match item categories")
        return self
