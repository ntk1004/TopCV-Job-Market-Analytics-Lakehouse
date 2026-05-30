from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .models import JobItem


def _first_text_driver(driver: WebDriver, selectors: tuple[str, ...]) -> str:
    for selector in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        if elements:
            text = elements[0].text.strip()
            if text:
                return text
    return ""

def get_job_info_value(driver: WebDriver, title_name: str) -> str:
    sections = driver.find_elements(
        By.CSS_SELECTOR,
        ".job-detail__info--section"
    )

    for section in sections:
        try:
            title = section.find_element(
                By.CSS_SELECTOR,
                ".job-detail__info--section-content-title"
            ).text.strip()

            if title.lower() == title_name.lower():
                value = section.find_element(
                    By.CSS_SELECTOR,
                    ".job-detail__info--section-content-value"
                ).text.strip()

                return value
        except Exception:
            continue

    return ""

def extract_job_url_from_card(card) -> str:
    link = card.find_element("css selector", "h3 a, a.job-link")
    return (link.get_attribute("href") or "").strip()


def _iter_job_description_sections(driver: WebDriver):
    items = driver.find_elements(
        By.CSS_SELECTOR,
        ".job-detail__information-detail--content .job-description__item",
    )
    if not items:
        items = driver.find_elements(By.CSS_SELECTOR, ".job-description__item")
    for item in items:
        h3_els = item.find_elements(By.CSS_SELECTOR, "h3")
        if not h3_els:
            continue
        heading = h3_els[0].text.strip()
        content_els = item.find_elements(By.CSS_SELECTOR, ".job-description__item--content")
        content = content_els[0].text.strip() if content_els else ""
        yield heading, content


def _location_from_sections(driver: WebDriver) -> str:
    for heading, content in _iter_job_description_sections(driver):
        if "Địa điểm" in heading:
            return content
    return ""

def _job_description_from_sections(driver: WebDriver) -> str:
    for heading, content in _iter_job_description_sections(driver):
        if "Mô tả công việc" in heading or "Mô tả" in heading:
            return content
    return ""

def _skills_from_sections(driver: WebDriver) -> str:
    for heading, content in _iter_job_description_sections(driver):
        if any(k in heading for k in ("Kỹ năng", "Công nghệ")) or "skill" in heading.lower():
            return content
    for heading, content in _iter_job_description_sections(driver):
        if "Yêu cầu" in heading:
            return content
    for heading, content in _iter_job_description_sections(driver):
        if "Mô tả công việc" in heading or "Mô tả" in heading:
            return content
    return ""


def _skills_from_tags(driver: WebDriver) -> str:
    for selector in (
        ".job-tags .tag",
        ".job-tags span",
        ".list-skill .item",
    ):
        els = driver.find_elements(By.CSS_SELECTOR, selector)
        parts = [e.text.strip() for e in els if e.text.strip()]
        if parts:
            return ", ".join(dict.fromkeys(parts))
    return ""


def parse_job_detail(driver: WebDriver, job_url: str, source_page: int) -> JobItem:
    title = _first_text_driver(
        driver,
        (
            "h1.job-title",
            ".job-detail__title h1",
            ".job-detail h1",
            "h1.title",
            "h1",
        ),
    )
    
    experience = get_job_info_value(driver, "Kinh nghiệm")

    company = _first_text_driver(
        driver,
        (
            ".company-name",
            ".company-name-lable",
            ".name-job-company",
            ".employer-name",
            "a.company-name",
        ),
    )
    location = _location_from_sections(driver) or _first_text_driver(
        driver,
        (".job-description__item--location", ".address", ".job-location"),
    )
    salary = get_job_info_value(driver, "Mức lương")
    
    skills = _skills_from_sections(driver) or _skills_from_tags(driver)
    
    job_description = _job_description_from_sections(driver)

    return JobItem(
        title=title,
        company=company,
        location=location,
        salary=salary,
        skills=skills,
        job_description=job_description,
        job_url=job_url,
        source_page=source_page,
        experience = experience
    )
