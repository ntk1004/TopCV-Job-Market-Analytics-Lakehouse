import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(slots=True)
class CrawlerConfig:
    base_url: str = field(
        default_factory=lambda: os.getenv("TOPCV_BASE_URL", "https://www.topcv.vn/viec-lam-it")
    )
    max_pages: int = field(default_factory=lambda: _env_int("TOPCV_MAX_PAGES", 3))
    headless: bool = field(default_factory=lambda: _env_bool("TOPCV_HEADLESS", True))
    page_load_timeout: int = 60  # Timeout for page load operations
    wait_timeout: int = 45  # Timeout for element wait operations
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    request_headers: dict[str, str] = field(
        default_factory=lambda: {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    card_selectors: tuple[str, ...] = (
        ".job-item-default",
        ".job-item-search-result",
        ".job-item",
    )
    debug_html_dir: Path = Path("pipelines/ingestion/craw_data/output/debug_html")
    detail_wait_selectors: tuple[str, ...] = (
        "h1",
        ".job-detail__information-detail--content",
        ".job-description",
        ".job-detail",
        ".box-job-info",
    )
    listing_max_wait_seconds: int = 180  # Increased to handle Cloudflare challenge
    cloudflare_poll_interval: float = 0.5  # Check more frequently
    after_navigation_sleep: float = 2.5  # Increased delays to be more human-like
    
