from pathlib import Path
from types import SimpleNamespace

from src.fetchers import rss_fetcher


def test_fetch_rss_sources_maps_source_metadata(tmp_path, make_settings, monkeypatch):
    sources_path = _write_sources(
        tmp_path,
        """
rss_sources:
  - name: Domestic Test
    url: https://example.com/rss.xml
    region: domestic_china
    language: zh
    weight: 1.25
    enabled: true
  - name: Disabled Test
    url: https://example.com/disabled.xml
    region: international
    language: en
    weight: 1.0
    enabled: false
""",
    )

    def fake_parse(url):
        assert url == "https://example.com/rss.xml"
        return SimpleNamespace(
            bozo=False,
            entries=[
                SimpleNamespace(
                    title="国内测试新闻",
                    link="https://example.com/news/1",
                    summary="摘要",
                    published_parsed=None,
                )
            ],
        )

    monkeypatch.setattr(rss_fetcher.feedparser, "parse", fake_parse)

    articles = rss_fetcher.fetch_rss_sources(make_settings(), sources_path)

    assert len(articles) == 1
    assert articles[0].source_name == "Domestic Test"
    assert articles[0].source_region == "domestic_china"
    assert articles[0].source_language == "zh"
    assert articles[0].source_weight == 1.25


def test_audit_rss_sources_reports_counts_and_titles(tmp_path, make_settings, monkeypatch):
    sources_path = _write_sources(
        tmp_path,
        """
rss_sources:
  - name: Audit Test
    url: https://example.com/rss.xml
    region: domestic_china
    language: zh
    weight: 1.0
    enabled: true
  - name: Disabled Audit Test
    url: ""
    region: international
    language: en
    weight: 1.0
    enabled: false
""",
    )

    def fake_parse(_url):
        return SimpleNamespace(
            bozo=False,
            entries=[
                SimpleNamespace(title="标题一", link="https://example.com/1", summary="摘要"),
                SimpleNamespace(title="标题二", link="https://example.com/2", summary="摘要"),
                SimpleNamespace(title="标题三", link="https://example.com/3", summary="摘要"),
                SimpleNamespace(title="标题四", link="https://example.com/4", summary="摘要"),
            ],
        )

    monkeypatch.setattr(rss_fetcher.feedparser, "parse", fake_parse)

    results = rss_fetcher.audit_rss_sources(make_settings(), sources_path)

    enabled_result = results[0]
    disabled_result = results[1]
    assert enabled_result["fetched_count"] == 4
    assert enabled_result["titles"] == ["标题一", "标题二", "标题三"]
    assert disabled_result["warning"] == "disabled"


def _write_sources(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sources.yaml"
    path.write_text(content, encoding="utf-8")
    return path
