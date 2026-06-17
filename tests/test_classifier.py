from src.processing.classifier import classify_items


def test_classifier_marks_china_news(make_article):
    article = make_article(
        title="Beijing announces new AI policy",
        raw_text="China is accelerating technology policy.",
    )

    result = classify_items([article])[0]

    assert result.category == "china"
    assert result.low_confidence is False


def test_classifier_marks_uncertain_as_international(make_article):
    article = make_article(
        title="Global climate summit opens in Brazil",
        category_hint="world",
        raw_text="Leaders discussed climate finance and disaster risk.",
    )

    result = classify_items([article])[0]

    assert result.category == "international"
    assert result.low_confidence is False


def test_classifier_low_confidence_for_weak_china_hint(make_article):
    article = make_article(
        title="Technology firms report earnings",
        category_hint="china",
        raw_text="The report focused on revenue and operations.",
    )

    result = classify_items([article])[0]

    assert result.category == "international"
    assert result.low_confidence is True
