"""DeepSeek client using the OpenAI-compatible SDK."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from src.config import Settings
from src.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from src.llm.schemas import Article, NewsReportOutput, normalize_report_payload

logger = logging.getLogger(__name__)


def create_deepseek_client(settings: Settings) -> OpenAI:
    return OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )


class DeepSeekClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )

    def analyze_news(
        self,
        articles: list[Article],
        generated_at: str,
        time_range_start: str,
        time_range_end: str,
    ) -> NewsReportOutput:
        if not self.settings.deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is required for --analyze-only.")

        system_prompt = SYSTEM_PROMPT
        user_prompt = self._build_user_prompt(
            articles=articles,
            generated_at=generated_at,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
        )

        allowed_source_urls = _allowed_source_urls(articles)
        allowed_image_urls = {article.image_url for article in articles if article.image_url}
        last_error: Exception | None = None

        for attempt in range(1, self.settings.deepseek_json_retry_times + 1):
            try:
                content = self._create_completion(system_prompt, user_prompt)
                if not content or not content.strip():
                    raise ValueError("DeepSeek returned empty content")

                payload = json.loads(content)
                payload = normalize_report_payload(payload)
                report = NewsReportOutput.model_validate(payload)
                if len(report.items) != len(articles):
                    raise ValueError(
                        f"DeepSeek returned {len(report.items)} items, expected {len(articles)}"
                    )
                self._validate_urls(report, allowed_source_urls, allowed_image_urls)
                return report
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "DeepSeek JSON analysis attempt %s/%s failed: %s",
                    attempt,
                    self.settings.deepseek_json_retry_times,
                    exc,
                )

        logger.error("DeepSeek analysis failed after all retries: %s", last_error)
        raise RuntimeError("DeepSeek analysis failed; report.json was not generated.") from last_error

    def _create_completion(self, system_prompt: str, user_prompt: str) -> str | None:
        kwargs: dict[str, Any] = {
            "model": self.settings.deepseek_model,
            "temperature": self.settings.deepseek_temperature,
            "max_tokens": self.settings.deepseek_max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        if self.settings.deepseek_thinking_enabled:
            kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
            kwargs["reasoning_effort"] = self.settings.deepseek_reasoning_effort

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def _build_user_prompt(
        self,
        articles: list[Article],
        generated_at: str,
        time_range_start: str,
        time_range_end: str,
    ) -> str:
        candidates = [_article_to_prompt_payload(article) for article in articles]
        return build_user_prompt(
            candidates=candidates,
            generated_at=generated_at,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            total_items=len(articles),
            china_min_ratio=self.settings.news_china_min_ratio,
            china_max_ratio=self.settings.news_china_max_ratio,
            max_images_per_item=self.settings.news_max_images_per_item,
        )

    def _validate_urls(
        self,
        report: NewsReportOutput,
        allowed_source_urls: set[str],
        allowed_image_urls: set[str],
    ) -> None:
        for item in report.items:
            for source in item.sources:
                if source.url not in allowed_source_urls:
                    raise ValueError(f"source url not in input candidates: {source.url}")
            for image in item.images:
                if image.image_url not in allowed_image_urls:
                    raise ValueError(f"image url not in input candidates: {image.image_url}")
                if image.source_url not in allowed_source_urls:
                    raise ValueError(f"image source_url not in input candidates: {image.source_url}")


def _article_to_prompt_payload(article: Article) -> dict[str, Any]:
    return {
        "title": article.title,
        "url": article.url,
        "source_name": article.source_name,
        "published_at": article.published_at,
        "category": article.category,
        "category_hint": article.category_hint,
        "importance_score_base": article.importance_score_base,
        "summary": article.summary,
        "raw_text": article.raw_text,
        "duplicate_sources": article.duplicate_sources,
        "image_url": article.image_url,
    }


def _allowed_source_urls(articles: list[Article]) -> set[str]:
    urls = {article.url for article in articles if article.url}
    for article in articles:
        urls.update(
            source
            for source in article.duplicate_sources
            if isinstance(source, str) and source.lower().startswith(("http://", "https://"))
        )
    return urls
