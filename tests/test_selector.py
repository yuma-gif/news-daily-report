from src.processing.selector import select_final_articles


def test_selector_picks_expected_region_mix_when_domestic_enough(make_article):
    candidates = (
        _articles(make_article, "domestic_china", 5, 90, "Domestic")
        + _articles(make_article, "china_related_international", 3, 80, "China Related")
        + _articles(make_article, "international", 10, 70, "International")
    )

    result = select_final_articles(candidates, total_items=12, domestic_min=4, china_related_max=2)

    assert len(result.articles) == 12
    assert result.domestic_shortage is False
    assert _count_region(result.articles, "domestic_china") == 4
    assert _count_region(result.articles, "china_related_international") == 2
    assert _count_region(result.articles, "international") == 6


def test_selector_records_domestic_shortage_and_fills_total(make_article):
    candidates = (
        _articles(make_article, "domestic_china", 2, 90, "Domestic")
        + _articles(make_article, "china_related_international", 3, 80, "China Related")
        + _articles(make_article, "international", 10, 70, "International")
    )

    result = select_final_articles(candidates, total_items=12, domestic_min=4, china_related_max=2)

    assert len(result.articles) == 12
    assert result.domestic_shortage is True
    assert _count_region(result.articles, "domestic_china") == 2


def test_selector_returns_all_when_candidates_less_than_total(make_article):
    candidates = _articles(make_article, "international", 5, 70, "International")

    result = select_final_articles(candidates, total_items=12, domestic_min=4, china_related_max=2)

    assert len(result.articles) == 5


def test_selector_excludes_soft_news_when_enough_hard_news(make_article):
    hard_news = (
        _articles(make_article, "domestic_china", 4, 90, "Domestic")
        + _articles(make_article, "china_related_international", 2, 80, "China Related")
        + _articles(make_article, "international", 6, 70, "International")
    )
    soft_news = [
        make_article(
            title="Celebrity singer opens fashion restaurant",
            url="https://example.com/soft",
            source_region="international",
            importance_score_base=999,
        )
    ]

    result = select_final_articles(soft_news + hard_news, total_items=12)

    assert len(result.articles) == 12
    assert all(article.url != "https://example.com/soft" for article in result.articles)


def _articles(make_article, region: str, count: int, start_score: float, prefix: str):
    topics = [
        "central bank policy",
        "court ruling",
        "climate disaster",
        "technology regulation",
        "trade sanctions",
        "public health reform",
        "energy security",
        "housing market",
        "education reform",
        "transport infrastructure",
        "fiscal budget",
        "supply chain",
    ]
    return [
        make_article(
            title=f"{prefix} {index}: {topics[index % len(topics)]}",
            url=f"https://example.com/{region}/{index}",
            source_region=region,
            importance_score_base=start_score - index,
        )
        for index in range(count)
    ]


def _count_region(articles, region: str) -> int:
    return sum(article.source_region == region for article in articles)
