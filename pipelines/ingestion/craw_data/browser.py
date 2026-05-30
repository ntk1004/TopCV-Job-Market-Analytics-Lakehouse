import os
import tempfile

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

from .config import CrawlerConfig


def build_driver(config: CrawlerConfig):
    """Build Chrome driver with anti-detection features."""
    options = Options()

    if config.headless:
        options.add_argument("--headless=new")

    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-agent={config.user_agent}")
    
    # Anti-detection: disable features that reveal automation
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Additional stealth options
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument(f"--user-data-dir={tempfile.mkdtemp(prefix='chrome-profile-')}")

    chrome_kwargs = {"options": options}
    chrome_bin = os.getenv("CHROME_BIN")
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    if chrome_bin:
        chrome_kwargs["browser_executable_path"] = chrome_bin
    if chromedriver_path:
        chrome_kwargs["driver_executable_path"] = chromedriver_path

    driver = uc.Chrome(**chrome_kwargs)
    
    # Inject JavaScript to mask navigator.webdriver
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            window.chrome = {
                runtime: {}
            };
        """
    })
    
    driver.set_page_load_timeout(config.page_load_timeout)
    return driver
