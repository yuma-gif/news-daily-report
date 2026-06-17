import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def setup_logging(logs_dir: Path | str = "logs", timezone_name: str = "Asia/Shanghai") -> Path:
    logs_path = Path(logs_dir)
    logs_path.mkdir(parents=True, exist_ok=True)
    run_log_path = logs_path / f"{datetime.now(ZoneInfo(timezone_name)).strftime('%Y%m%d_%H%M')}.log"

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(run_log_path, encoding="utf-8"),
        ],
    )
    return run_log_path
