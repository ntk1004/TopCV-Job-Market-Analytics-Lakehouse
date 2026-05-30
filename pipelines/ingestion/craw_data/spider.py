from __future__ import annotations

import time
from urllib.parse import parse_qs, urlencode, urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from .browser import build_driver
from .config import CrawlerConfig
from .parser import extract_job_url_from_card, parse_job_detail


class TopCVSpider:
    def __init__(self, config: CrawlerConfig) -> None:
        self.config = config

    def _build_page_url(self, page: int) -> str:
        if page <= 1:
            return self.config.base_url
        query = urlencode({"page": page})
        return f"{self.config.base_url}?{query}"

    def _find_cards(self, driver):
        for selector in self.config.card_selectors:
            cards = driver.find_elements(By.CSS_SELECTOR, selector)
            if cards:
                return cards
        return []

    def _is_cloudflare_interstitial(self, driver) -> bool:
        try:
            title = (driver.title or "").lower()
            if "just a moment" in title:
                return True
        except TimeoutException:
            # Timeout accessing title indicates potential Cloudflare issue
            return True
        except Exception:
            pass
        
        src = ""
        try:
            src = driver.page_source[:4000].lower()
        except TimeoutException:
            # If we can't get page source, assume it's a Cloudflare block
            return True
        except Exception:
            return False
        
        return (
            "challenges.cloudflare.com" in src
            or "security verification" in src
            or "cf-chl" in src
            or "turnstile" in src
        )

    def _wait_listing_ready(self, driver) -> bool:
        deadline = time.monotonic() + self.config.listing_max_wait_seconds
        last_cloudflare_check = 0
        
        while time.monotonic() < deadline:
            try:
                # Check for Cloudflare interstitial
                if time.monotonic() - last_cloudflare_check > self.config.cloudflare_poll_interval:
                    try:
                        if self._is_cloudflare_interstitial(driver):
                            last_cloudflare_check = time.monotonic()
                            time.sleep(self.config.cloudflare_poll_interval)
                            continue
                    except Exception:
                        pass
                    last_cloudflare_check = time.monotonic()
                
                # Check if cards are loaded
                cards = self._find_cards(driver)
                if cards:
                    return True
                
                time.sleep(self.config.cloudflare_poll_interval)
            except TimeoutException:
                # If we hit timeout, wait a bit and retry
                time.sleep(self.config.cloudflare_poll_interval)
                continue
        
        return bool(self._find_cards(driver))

    def _open_listing_page(self, driver, page: int) -> bool:
        driver.get(self._build_page_url(1))
        time.sleep(self.config.after_navigation_sleep)
        if not self._wait_listing_ready(driver):
            return False
        if page <= 1:
            return True

        link = self._find_pagination_link(driver, page)
        if link is not None:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", link)
            except Exception:
                driver.get(self._build_page_url(page))
        else:
            driver.get(self._build_page_url(page))
        time.sleep(self.config.after_navigation_sleep)
        return self._wait_listing_ready(driver)

    def _find_pagination_link(self, driver, page: int):
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='page=']"):
            href = (a.get_attribute("href") or "").strip()
            if not href:
                continue
            try:
                q = parse_qs(urlparse(href).query).get("page", [])
                if q and q[0] == str(page):
                    return a
            except Exception:
                continue
        return None

    def _wait_detail_loaded(self, driver) -> None:
        try:
            WebDriverWait(driver, self.config.wait_timeout).until(
                lambda d: any(
                    d.find_elements(By.CSS_SELECTOR, sel)
                    for sel in self.config.detail_wait_selectors
                )
            )
        except TimeoutException:
            # If detail elements don't load, try to parse anyway
            # (page might have loaded with different structure)
            pass

    def crawl(self):
        driver = build_driver(self.config)
        items: list[dict] = []
        self.config.debug_html_dir.mkdir(parents=True, exist_ok=True)
        try:
            for page in range(1, self.config.max_pages + 1):
                if not self._open_listing_page(driver, page):
                    debug_file = self.config.debug_html_dir / f"list_page_{page}.html"
                    debug_file.write_text(driver.page_source, encoding="utf-8")
                    print(f"[WARN] Listing page {page} not ready, saved: {debug_file}")
                    continue

                cards = self._find_cards(driver)
                if not cards:
                    debug_file = self.config.debug_html_dir / f"list_empty_{page}.html"
                    debug_file.write_text(driver.page_source, encoding="utf-8")
                    print(f"[WARN] No job cards on page {page}, saved: {debug_file}")
                    continue

                job_urls: list[str] = []
                for card in cards:
                    try:
                        href = extract_job_url_from_card(card)
                        if href and href not in job_urls:
                            job_urls.append(href)
                    except Exception:
                        continue

                for job_url in job_urls:
                    try:
                        driver.get(job_url)
                        time.sleep(self.config.after_navigation_sleep)
                        
                        # Check if page is blocked by Cloudflare
                        if self._is_cloudflare_interstitial(driver):
                            print(f"[WARN] Cloudflare block on detail page {job_url}")
                            continue
                        
                        self._wait_detail_loaded(driver)
                        job_item = parse_job_detail(driver, job_url, source_page=page)
                        
                        # Skip if title is empty or is the Cloudflare challenge page title
                        if not job_item.title or job_item.title == "www.topcv.vn":
                            print(f"[WARN] Empty or invalid job data for {job_url}")
                            continue
                        
                        items.append(job_item.to_dict())
                    except TimeoutException:
                        debug_file = (
                            self.config.debug_html_dir
                            / f"detail_timeout_{abs(hash(job_url)) % 10_000_000}.html"
                        )
                        debug_file.write_text(driver.page_source, encoding="utf-8")
                        print(f"[WARN] Timeout detail {job_url}, saved: {debug_file}")
                    except Exception:
                        continue
        finally:
            driver.quit()

        return items
