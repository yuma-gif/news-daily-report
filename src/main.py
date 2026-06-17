import argparse
import json
import logging
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.config import load_settings
from src.fetchers.rss_fetcher import audit_rss_sources, fetch_rss_sources
from src.llm.deepseek_client import DeepSeekClient
from src.llm.schemas import Article
from src.processing.classifier import classify_items
from src.processing.content_extractor import enrich_articles_with_raw_text
from src.processing.deduplicate import deduplicate_items
from src.processing.ranker import rank_items
from src.processing.selector import SelectionResult, select_final_articles
from src.render.docx_writer import write_docx_report
from src.utils.logger import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="News daily report generator")
    parser.add_argument("--fetch-only", action="store_true", help="Fetch RSS articles only")
    parser.add_argument(
        "--process-only",
        action="store_true",
        help="Process the latest raw RSS JSON into ranked candidates",
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Analyze the latest processed candidates with DeepSeek",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selected analysis candidates without calling DeepSeek",
    )
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Render the latest structured report JSON into a Word document",
    )
    parser.add_argument(
        "--source-audit",
        action="store_true",
        help="Audit configured RSS sources without generating reports",
    )
    args = parser.parse_args()

    settings = load_settings()
    run_log_path = setup_logging(settings.logs_dir, settings.news_timezone)
    logger.info("Run log: %s", run_log_path)

    try:
        if args.source_audit:
            _run_source_audit(settings)
            return

        if args.fetch_only:
            _run_fetch_step(settings)
            return

        if args.process_only:
            raw_path = _find_latest_raw_articles()
            _run_process_step(settings, raw_path)
            return

        if args.analyze_only:
            candidates_path = _find_latest_candidates()
            report_path = _run_analyze_step(settings, candidates_path, args.dry_run)
            if report_path is not None:
                print(f"DeepSeek report saved to: {report_path}")
            return

        if args.render_only:
            report_path = _find_latest_report()
            save_path = _run_render_step(settings, report_path)
            print(f"Word report saved to: {save_path}")
            return

        raw_path = _run_fetch_step(settings)
        candidates_path = _run_process_step(settings, raw_path)
        report_path = _run_analyze_step(settings, candidates_path, args.dry_run)
        if args.dry_run:
            logger.info("Dry-run complete. DeepSeek was not called and Word rendering was skipped.")
            return
        save_path = _run_render_step(settings, report_path)
        print(f"Word report saved to: {save_path}")
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        raise SystemExit(1) from exc


def _run_fetch_step(settings) -> Path:
    logger.info("Step fetch started")
    try:
        articles = fetch_rss_sources(settings)
        save_path = _save_raw_articles(articles, settings.news_timezone)
        _log_fetch_summary(articles, save_path)
        logger.info("Step fetch finished")
        return save_path
    except Exception as exc:
        logger.exception("Step fetch failed: %s", exc)
        raise


def _run_source_audit(settings) -> None:
    logger.info("Source audit started")
    audit_results = audit_rss_sources(settings)
    region_counts = Counter()

    for result in audit_results:
        region = result.get("region") or "unknown"
        region_counts[region] += int(result.get("fetched_count") or 0)
        warning = result.get("warning") or ""
        titles = result.get("titles") or []
        logger.info(
            "source=%s region=%s language=%s enabled=%s fetched_count=%s warning=%s",
            result.get("name"),
            region,
            result.get("language"),
            result.get("enabled"),
            result.get("fetched_count"),
            warning,
        )
        print(
            f"{result.get('name')} | region={region} | language={result.get('language')} "
            f"| enabled={result.get('enabled')} | fetched_count={result.get('fetched_count')} "
            f"| warning={warning}"
        )
        for index, title in enumerate(titles[:3], start=1):
            print(f"  [{index}] {title}")

    print(f"Total domestic_china: {region_counts.get('domestic_china', 0)}")
    print(
        "Total china_related_international: "
        f"{region_counts.get('china_related_international', 0)}"
    )
    print(f"Total international: {region_counts.get('international', 0)}")
    logger.info("Source audit finished")


def _run_process_step(settings, raw_path: Path) -> Path:
    logger.info("Step process started: %s", raw_path)
    try:
        raw_articles = _load_articles(raw_path)
        enriched_articles = enrich_articles_with_raw_text(raw_articles)
        deduplicated_articles = deduplicate_items(enriched_articles)
        classified_articles = classify_items(deduplicated_articles)
        ranked_articles = rank_items(classified_articles)
        save_path = _save_processed_candidates(ranked_articles, settings.news_timezone)
        _log_process_summary(raw_articles, deduplicated_articles, ranked_articles, save_path)
        logger.info("Step process finished")
        return save_path
    except Exception as exc:
        logger.exception("Step process failed: %s", exc)
        raise


def _run_analyze_step(settings, candidates_path: Path, dry_run: bool) -> Path | None:
    logger.info("Step analyze started: %s", candidates_path)
    try:
        candidates = _load_articles(candidates_path)
        selection = select_final_articles(
            candidates,
            total_items=settings.news_total_items,
            domestic_min=4,
            china_related_max=2,
        )
        selected_articles = selection.articles
        _log_selection_summary(selection, settings.news_total_items)
        generated_at, time_range_start, time_range_end = _analysis_time_range(settings)

        if dry_run:
            _log_deepseek_dry_run(candidates_path, selection)
            logger.info("Step analyze dry-run finished")
            return None

        report = DeepSeekClient(settings).analyze_news(
            articles=selected_articles,
            generated_at=generated_at,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
        )
        save_path = _save_report(report, settings.news_timezone)
        logger.info("Saved DeepSeek report to: %s", save_path)
        logger.info("Step analyze finished")
        return save_path
    except Exception as exc:
        logger.exception("Step analyze failed: %s", exc)
        raise


def _run_render_step(settings, report_path: Path) -> Path:
    logger.info("Step render started: %s", report_path)
    try:
        report = _load_report(report_path)
        save_path = write_docx_report(report, settings)
        logger.info("Saved Word report to: %s", save_path)
        logger.info("Step render finished")
        return save_path
    except Exception as exc:
        logger.exception("Step render failed: %s", exc)
        raise


def _log_fetch_summary(articles: list[Article], save_path: Path) -> None:
    source_counts = Counter(article.source_name for article in articles)
    missing_published_count = sum(article.missing_published_at for article in articles)
    logger.info("Total fetched articles: %s", len(articles))
    for source_name, count in sorted(source_counts.items()):
        logger.info("Fetched from %s: %s", source_name, count)
    logger.info("Missing published_at count: %s", missing_published_count)
    logger.info("Saved raw articles to: %s", save_path)


def _log_process_summary(
    raw_articles: list[Article],
    deduplicated_articles: list[Article],
    ranked_articles: list[Article],
    save_path: Path,
) -> None:
    category_counts = Counter(article.category for article in ranked_articles)
    logger.info("Raw article count: %s", len(raw_articles))
    logger.info("Deduplicated article count: %s", len(deduplicated_articles))
    logger.info("China count: %s", category_counts.get("china", 0))
    logger.info("International count: %s", category_counts.get("international", 0))
    logger.info("Top 20 candidates:")
    for index, article in enumerate(ranked_articles[:20], start=1):
        logger.info(
            "%02d. [%.2f] %s",
            index,
            article.importance_score_base or 0,
            article.title,
        )
    logger.info("Saved processed candidates to: %s", save_path)


def _log_selection_summary(selection: SelectionResult, total_items: int) -> None:
    counts = Counter(_article_region(article) for article in selection.articles)
    logger.info("Selected final article count: %s/%s", len(selection.articles), total_items)
    logger.info("Selected domestic_china count: %s", counts.get("domestic_china", 0))
    logger.info(
        "Selected china_related_international count: %s",
        counts.get("china_related_international", 0),
    )
    logger.info("Selected international count: %s", counts.get("international", 0))
    if selection.domestic_shortage:
        logger.warning("Domestic China shortage: fewer than 4 domestic_china candidates selected")


def _log_deepseek_dry_run(candidates_path: Path, selection: SelectionResult) -> None:
    selected_articles = selection.articles
    logger.info("DeepSeek dry-run candidate submission preview:")
    logger.info("Candidates file: %s", candidates_path)
    logger.info("Selected candidate count: %s", len(selected_articles))
    for region in ("domestic_china", "china_related_international", "international"):
        grouped_articles = [article for article in selected_articles if _article_region(article) == region]
        logger.info("%s count: %s", region, len(grouped_articles))
        print(f"{region} ({len(grouped_articles)}):")
        for index, article in enumerate(grouped_articles, start=1):
            line = (
                f"  {index}. [{article.importance_score_base or 0:.2f}] "
                f"{article.title} | source={article.source_name}"
            )
            print(line)
            logger.info(
                "%s %02d. [%.2f] %s | source=%s | duplicate_sources=%s",
                region,
                index,
                article.importance_score_base or 0,
                article.title,
                article.source_name,
                article.duplicate_sources,
            )
    if selection.domestic_shortage:
        print("WARNING: domestic_china candidates fewer than target 4; filled with other regions.")


def _article_region(article: Article) -> str:
    if article.source_region:
        return article.source_region
    if article.category == "china":
        return "domestic_china"
    return "international"


def _save_raw_articles(articles: list, timezone_name: str) -> Path:
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(ZoneInfo(timezone_name)).strftime("%Y%m%d_%H%M")
    save_path = raw_dir / f"{timestamp}_articles.json"
    payload = [
        article.model_dump(mode="json") if hasattr(article, "model_dump") else article
        for article in articles
    ]

    with save_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    return save_path


def _find_latest_raw_articles() -> Path:
    raw_files = sorted(Path("data/raw").glob("*_articles.json"))
    if not raw_files:
        raise FileNotFoundError("No raw article JSON files found in data/raw.")
    return raw_files[-1]


def _find_latest_candidates() -> Path:
    candidate_files = sorted(Path("data/processed").glob("*_candidates.json"))
    if not candidate_files:
        raise FileNotFoundError("No candidate JSON files found in data/processed.")
    return candidate_files[-1]


def _find_latest_report() -> Path:
    report_files = sorted(Path("data/processed").glob("*_report.json"))
    if not report_files:
        raise FileNotFoundError("No report JSON files found in data/processed.")
    return report_files[-1]


def _load_articles(path: Path) -> list[Article]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return [Article.model_validate(item) for item in payload]


def _load_report(path: Path):
    from src.llm.schemas import NewsReportOutput

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return NewsReportOutput.model_validate(payload)


def _save_processed_candidates(articles: list[Article], timezone_name: str) -> Path:
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(ZoneInfo(timezone_name)).strftime("%Y%m%d_%H%M")
    save_path = processed_dir / f"{timestamp}_candidates.json"
    payload = [article.model_dump(mode="json") for article in articles]

    with save_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    return save_path


def _analysis_time_range(settings) -> tuple[str, str, str]:
    now = datetime.now(ZoneInfo(settings.news_timezone))
    start = now - timedelta(hours=settings.news_lookback_hours)
    return now.isoformat(), start.isoformat(), now.isoformat()


def _save_report(report, timezone_name: str) -> Path:
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(ZoneInfo(timezone_name)).strftime("%Y%m%d_%H%M")
    save_path = processed_dir / f"{timestamp}_report.json"

    with save_path.open("w", encoding="utf-8") as file:
        json.dump(report.model_dump(mode="json"), file, ensure_ascii=False, indent=2)

    return save_path


if __name__ == "__main__":
    main()
