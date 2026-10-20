"""Unit tests for HTTP crawler and security guards."""

import pytest
from src.crawler import BookCatalogCrawler
from src.models import ScraperConfig


def test_crawler_rejects_unsafe_scheme() -> None:
    config = ScraperConfig(start_url="https://books.toscrape.com")
    crawler = BookCatalogCrawler(config)

    with pytest.raises(ValueError, match="Unsupported or unsafe URL scheme"):
        crawler.fetch_page_html("file:///etc/passwd")

    with pytest.raises(ValueError, match="Unsupported or unsafe URL scheme"):
        crawler.fetch_page_html("ftp://example.com/data")


def test_scraper_config_validates_start_url() -> None:
    with pytest.raises(ValueError, match="start_url must be an HTTP or HTTPS URL"):
        ScraperConfig(start_url="javascript:alert(1)")

    with pytest.raises(ValueError, match="start_url must be an HTTP or HTTPS URL"):
        ScraperConfig(start_url="file:///etc/shadow")
