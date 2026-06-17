import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    deepseek_temperature: float
    deepseek_max_tokens: int
    deepseek_json_retry_times: int
    deepseek_thinking_enabled: bool
    deepseek_reasoning_effort: str
    news_output_dir: Path
    news_timezone: str
    news_target_hour: int
    news_total_items: int
    news_china_min_ratio: float
    news_china_max_ratio: float
    news_lookback_hours: int
    news_max_images_per_item: int
    logs_dir: Path = Path("logs")


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        deepseek_temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", "0.2")),
        deepseek_max_tokens=int(os.getenv("DEEPSEEK_MAX_TOKENS", "12000")),
        deepseek_json_retry_times=int(os.getenv("DEEPSEEK_JSON_RETRY_TIMES", "3")),
        deepseek_thinking_enabled=_get_bool("DEEPSEEK_THINKING_ENABLED", False),
        deepseek_reasoning_effort=os.getenv("DEEPSEEK_REASONING_EFFORT", "medium"),
        news_output_dir=Path(os.getenv("NEWS_OUTPUT_DIR", "output")),
        news_timezone=os.getenv("NEWS_TIMEZONE", "Asia/Shanghai"),
        news_target_hour=int(os.getenv("NEWS_TARGET_HOUR", "8")),
        news_total_items=int(os.getenv("NEWS_TOTAL_ITEMS", "12")),
        news_china_min_ratio=float(os.getenv("NEWS_CHINA_MIN_RATIO", "0.30")),
        news_china_max_ratio=float(os.getenv("NEWS_CHINA_MAX_RATIO", "0.40")),
        news_lookback_hours=int(os.getenv("NEWS_LOOKBACK_HOURS", "24")),
        news_max_images_per_item=int(os.getenv("NEWS_MAX_IMAGES_PER_ITEM", "3")),
    )
