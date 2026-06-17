import json

import pytest

from src.llm.deepseek_client import DeepSeekClient


def test_deepseek_client_parses_valid_json(make_article, make_settings, make_report_payload):
    article = make_article(url="https://example.com/news/1")
    client = DeepSeekClient(make_settings())
    payload = make_report_payload(source_url=article.url)
    client._create_completion = lambda *_args, **_kwargs: json.dumps(payload, ensure_ascii=False)

    report = client.analyze_news(
        [article],
        generated_at=payload["generated_at"],
        time_range_start=payload["time_range_start"],
        time_range_end=payload["time_range_end"],
    )

    assert report.total_items == 1
    assert report.items[0].sources[0].url == article.url


def test_deepseek_client_retries_empty_content(make_article, make_settings, make_report_payload):
    article = make_article(url="https://example.com/news/1")
    client = DeepSeekClient(make_settings())
    payload = make_report_payload(source_url=article.url)
    responses = iter(["", json.dumps(payload, ensure_ascii=False)])
    client._create_completion = lambda *_args, **_kwargs: next(responses)

    report = client.analyze_news(
        [article],
        generated_at=payload["generated_at"],
        time_range_start=payload["time_range_start"],
        time_range_end=payload["time_range_end"],
    )

    assert report.items[0].title == "香港重大新闻"


def test_deepseek_client_retries_invalid_json(make_article, make_settings, make_report_payload):
    article = make_article(url="https://example.com/news/1")
    client = DeepSeekClient(make_settings())
    payload = make_report_payload(source_url=article.url)
    responses = iter(["not json", json.dumps(payload, ensure_ascii=False)])
    client._create_completion = lambda *_args, **_kwargs: next(responses)

    report = client.analyze_news(
        [article],
        generated_at=payload["generated_at"],
        time_range_start=payload["time_range_start"],
        time_range_end=payload["time_range_end"],
    )

    assert report.total_items == 1


def test_deepseek_client_adds_limited_source_uncertainty(
    make_article,
    make_settings,
    make_report_payload,
):
    article = make_article(url="https://example.com/news/1")
    client = DeepSeekClient(make_settings())
    payload = make_report_payload(source_url=article.url)
    payload["items"][0]["uncertainties"] = ["后续调查结论仍可能变化"]
    client._create_completion = lambda *_args, **_kwargs: json.dumps(payload, ensure_ascii=False)

    report = client.analyze_news(
        [article],
        generated_at=payload["generated_at"],
        time_range_start=payload["time_range_start"],
        time_range_end=payload["time_range_end"],
    )

    assert "该事件目前仅有一个来源" in report.items[0].uncertainties[-1]


def test_deepseek_client_normalizes_float_importance_score(
    make_article,
    make_settings,
    make_report_payload,
):
    article = make_article(url="https://example.com/news/1")
    client = DeepSeekClient(make_settings())
    payload = make_report_payload(source_url=article.url)
    payload["items"][0]["importance_score"] = 28.75
    client._create_completion = lambda *_args, **_kwargs: json.dumps(payload, ensure_ascii=False)

    report = client.analyze_news(
        [article],
        generated_at=payload["generated_at"],
        time_range_start=payload["time_range_start"],
        time_range_end=payload["time_range_end"],
    )

    assert report.items[0].importance_score == 29


def test_deepseek_client_recalculates_category_counts(
    make_article,
    make_settings,
    make_report_payload,
):
    article = make_article(url="https://example.com/news/1")
    client = DeepSeekClient(make_settings())
    payload = make_report_payload(source_url=article.url)
    payload["total_items"] = 99
    payload["china_items"] = 0
    payload["international_items"] = 99
    client._create_completion = lambda *_args, **_kwargs: json.dumps(payload, ensure_ascii=False)

    report = client.analyze_news(
        [article],
        generated_at=payload["generated_at"],
        time_range_start=payload["time_range_start"],
        time_range_end=payload["time_range_end"],
    )

    assert report.total_items == 1
    assert report.china_items == 1
    assert report.international_items == 0


def test_deepseek_client_normalizes_string_importance_score(
    make_article,
    make_settings,
    make_report_payload,
):
    article = make_article(url="https://example.com/news/1")
    client = DeepSeekClient(make_settings())
    payload = make_report_payload(source_url=article.url)
    payload["items"][0]["importance_score"] = "101.2"
    client._create_completion = lambda *_args, **_kwargs: json.dumps(payload, ensure_ascii=False)

    report = client.analyze_news(
        [article],
        generated_at=payload["generated_at"],
        time_range_start=payload["time_range_start"],
        time_range_end=payload["time_range_end"],
    )

    assert report.items[0].importance_score == 100


def test_deepseek_client_fills_missing_importance_score(
    make_article,
    make_settings,
    make_report_payload,
):
    article = make_article(url="https://example.com/news/1")
    client = DeepSeekClient(make_settings())
    payload = make_report_payload(source_url=article.url)
    del payload["items"][0]["importance_score"]
    payload["items"][0]["rank"] = 3
    client._create_completion = lambda *_args, **_kwargs: json.dumps(payload, ensure_ascii=False)

    report = client.analyze_news(
        [article],
        generated_at=payload["generated_at"],
        time_range_start=payload["time_range_start"],
        time_range_end=payload["time_range_end"],
    )

    assert report.items[0].importance_score == 79


def test_deepseek_client_fails_when_source_url_not_in_input(
    make_article,
    make_settings,
    make_report_payload,
):
    article = make_article(url="https://example.com/news/1")
    settings = make_settings()
    settings = settings.__class__(**{**settings.__dict__, "deepseek_json_retry_times": 2})
    client = DeepSeekClient(settings)
    payload = make_report_payload(source_url="https://not-allowed.example.com/news")
    client._create_completion = lambda *_args, **_kwargs: json.dumps(payload, ensure_ascii=False)

    with pytest.raises(RuntimeError):
        client.analyze_news(
            [article],
            generated_at=payload["generated_at"],
            time_range_start=payload["time_range_start"],
            time_range_end=payload["time_range_end"],
        )
