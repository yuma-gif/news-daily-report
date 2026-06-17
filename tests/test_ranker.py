from src.processing.ranker import rank_items


def test_ranker_scores_high_authority_major_news_above_minor_news(make_article):
    major = make_article(
        title="Central bank sanctions follow war escalation",
        source_name="Reuters World",
        raw_text="war sanctions central bank election court climate finance " * 20,
        duplicate_sources=["BBC World", "AP News"],
        image_url="https://example.com/image.jpg",
    )
    minor = make_article(
        title="Local festival opens",
        source_name="CGTN",
        raw_text="short local event",
    )

    ranked = rank_items([minor, major])

    assert ranked[0] is major
    assert major.importance_score_base is not None
    assert minor.importance_score_base is not None
    assert major.importance_score_base > minor.importance_score_base
