"""HTTP crawler and session manager with retries, throttling, and pagination."""

import logging
import random
import time
from typing import Callable, Iterator
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from src.models import BookItem, ScraperConfig
from src.parser import extract_books, extract_next_page

logger = logging.getLogger(__name__)


MAX_RESPONSE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit per page


class BookCatalogCrawler:
    """Manages HTTP requests, exponential backoff retries, and pagination."""

    def __init__(self, config: ScraperConfig) -> None:
        """Initialize crawler session with retry configuration.

        Args:
            config: Scraper configuration parameters.
        """
        self.config = config
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        """Build requests session with custom headers and exponential backoff.

        Returns:
            Configured requests.Session instance.
        """
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self.config.user_agent,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

        retry_strategy = Retry(
            total=3,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _polite_delay(self) -> None:
        """Sleep for a randomized duration between configured delay bounds."""
        delay = random.uniform(self.config.delay_min, self.config.delay_max)
        logger.debug("Throttling request for %.2f seconds", delay)
        time.sleep(delay)

    def fetch_page_html(self, url: str) -> str:
        """Fetch HTML content from a given URL with timeout and error handling.

        Args:
            url: Page URL to fetch.

        Returns:
            Decoded HTML string.

        Raises:
            ValueError: If URL scheme is unsupported or payload exceeds size limit.
            requests.RequestException: If the HTTP request fails.
        """
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError(f"Unsupported or unsafe URL scheme: '{url}'")

        self._polite_delay()
        logger.info("Fetching: %s", url)
        response = self.session.get(url, timeout=self.config.timeout, stream=True)
        response.raise_for_status()

        # Enforce maximum response size to prevent decompression bombs / OOM
        content_chunks: list[bytes] = []
        bytes_received = 0
        for chunk in response.iter_content(chunk_size=65536):
            if chunk:
                bytes_received += len(chunk)
                if bytes_received > MAX_RESPONSE_BYTES:
                    raise ValueError(f"Response size exceeded safety limit of {MAX_RESPONSE_BYTES} bytes")
                content_chunks.append(chunk)

        raw_bytes = b"".join(content_chunks)
        encoding = response.encoding or response.apparent_encoding or "utf-8"
        return raw_bytes.decode(encoding, errors="replace")

    def crawl_catalog(
        self,
        on_page_start: Callable[[int, str], None] | None = None,
        on_page_complete: Callable[[int, str, list[BookItem]], None] | None = None,
    ) -> Iterator[tuple[str, list[BookItem]]]:
        """Crawl the catalog page by page yielding discovered book items.

        Args:
            on_page_start: Optional callback before fetching a page: (page_num, url).
            on_page_complete: Optional callback after extracting books: (page_num, url, items).

        Yields:
            Tuples of (page_url, list_of_books_on_page).
        """
        current_url: str | None = self.config.start_url
        page_num = 1
        max_pages = self.config.max_pages

        while current_url:
            if max_pages > 0 and page_num > max_pages:
                logger.info("Reached maximum configured pages limit: %d", max_pages)
                break

            if on_page_start:
                on_page_start(page_num, current_url)

            try:
                html = self.fetch_page_html(current_url)
            except requests.RequestException as err:
                logger.error("Failed to fetch page %d (%s): %s", page_num, current_url, err)
                break

            books = extract_books(html, current_url)
            logger.info("Page %d yielded %d books", page_num, len(books))

            if on_page_complete:
                on_page_complete(page_num, current_url, books)

            yield (current_url, books)

            next_url = extract_next_page(html, current_url)
            if not next_url:
                logger.info("No next page link found; catalog traversal complete.")
                break

            current_url = next_url
            page_num += 1

    def close(self) -> None:
        """Close the underlying requests session."""
        self.session.close()
