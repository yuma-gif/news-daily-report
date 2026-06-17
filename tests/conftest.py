from pathlib import Path

import pytest

from src.config import Settings
from src.llm.schemas import Article


@pytest.fixture
def make_article(
) -> callable:
    def _make_article(
        title: str = "Global market update",
        url: str = "https://example.com/news/1",
        source_name: str = "BBC World",
        raw_text: str | None = "A detailed article body about markets and policy.",
        summary: str | None = "A short summary.",
        category_hint: str | None = "world",
        source_region: str | None = None,
        source_language: str | None = None,
        source_weight: float | None = None,
        importance_score_base: float | None = None,
        duplicate_sources: list[str] | None = None,
        image_url: str | None = None,
    ) -> Article:
        return Article(
            title=title,
            url=url,
            source_name=source_name,
            source_region=source_region,
            source_language=source_language,
            source_weight=source_weight,
            published_at="2026-06-11T08:00:00+08:00",
            summary=summary,
            category_hint=category_hint,
            image_url=image_url,
            raw_text=raw_text,
            duplicate_sources=duplicate_sources or [],
            importance_score_base=importance_score_base,
        )

    return _make_article


@pytest.fixture
def make_settings(tmp_path: Path) -> callable:
    def _make_settings(output_root: Path | None = None) -> Settings:
        root = output_root or tmp_path
        return Settings(
            deepseek_api_key="test-key",
            deepseek_base_url="https://api.deepseek.com",
            deepseek_model="deepseek-v4-flash",
            deepseek_temperature=0.2,
            deepseek_max_tokens=12000,
            deepseek_json_retry_times=3,
            deepseek_thinking_enabled=False,
            deepseek_reasoning_effort="medium",
            news_output_dir=root / "output",
            news_timezone="Asia/Shanghai",
            news_target_hour=8,
            news_total_items=12,
            news_china_min_ratio=0.30,
            news_china_max_ratio=0.40,
            news_lookback_hours=24,
            news_max_images_per_item=3,
            logs_dir=root / "logs",
        )

    return _make_settings


@pytest.fixture
def make_report_payload(source_url: str = "https://example.com/news/1") -> dict:
    def _make_report_payload(source_url: str = "https://example.com/news/1") -> dict:
        return {
            "generated_at": "2026-06-11T08:00:00+08:00",
            "time_range_start": "2026-06-10T08:00:00+08:00",
            "time_range_end": "2026-06-11T08:00:00+08:00",
            "total_items": 1,
            "china_items": 1,
            "international_items": 0,
            "items": [
                {
                    "rank": 1,
                    "title": "香港重大新闻",
                    "category": "china",
                    "importance_score": 88,
                    "summary": "这是一条用于测试的中文新闻概要。",
                    "detailed_report": "这是一段综合报道，用于测试 Word 渲染和 JSON 解析。",
                    "positive_impacts": ["提高公共安全关注度"],
                    "negative_impacts": ["可能造成社会焦虑"],
                    "risks": ["后续调查仍有不确定性"],
                    "uncertainties": ["来源较少，仍需等待更多官方信息"],
                    "lessons": ["可复用的观察或启示"],
                    "sources": [
                        {
                            "source_name": "BBC World",
                            "title": "香港重大新闻",
                            "url": source_url,
                        }
                    ],
                    "images": [],
                }
            ],
        }

    return _make_report_payload
