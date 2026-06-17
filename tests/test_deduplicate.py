from src.processing.deduplicate import deduplicate_items


def test_deduplicate_by_similar_title_keeps_better_source(make_article):
    articles = [
        make_article(
            title="Trump and Iran trade new threats after strikes exchanged",
            url="https://example.com/a",
            source_name="CGTN",
            raw_text="short",
        ),
        make_article(
            title="Trump and Iran trade new threats after strikes",
            url="https://example.com/b",
            source_name="BBC World",
            raw_text="longer and more complete body text",
        ),
    ]

    result = deduplicate_items(articles)

    assert len(result) == 1
    assert result[0].source_name == "BBC World"
    assert "CGTN" in result[0].duplicate_sources
