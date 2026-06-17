"""Image download and resizing helpers for DOCX rendering."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image

from src.llm.schemas import ImageOutput

logger = logging.getLogger(__name__)

MAX_IMAGE_WIDTH_PX = 900
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = "NewsMVP/0.1 (+https://local.news.mvp)"


def prepare_image(image: ImageOutput, cache_dir: Path | str = "data/cache/images") -> Path | None:
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    suffix = _guess_suffix(image.image_url)
    filename = hashlib.sha256(image.image_url.encode("utf-8")).hexdigest()[:24] + suffix
    output_path = cache_path / filename

    if output_path.exists():
        return output_path

    try:
        response = requests.get(
            image.image_url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to download image %s: %s", image.image_url, exc)
        return None

    try:
        temp_path = output_path.with_suffix(".download")
        temp_path.write_bytes(response.content)
        with Image.open(temp_path) as img:
            img = img.convert("RGB")
            if img.width > MAX_IMAGE_WIDTH_PX:
                ratio = MAX_IMAGE_WIDTH_PX / img.width
                img = img.resize((MAX_IMAGE_WIDTH_PX, max(1, int(img.height * ratio))))
            output_path = output_path.with_suffix(".jpg")
            img.save(output_path, format="JPEG", quality=88, optimize=True)
        temp_path.unlink(missing_ok=True)
        return output_path
    except Exception as exc:
        logger.warning("Failed to process image %s: %s", image.image_url, exc)
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        return None


def _guess_suffix(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return suffix
    return ".jpg"
