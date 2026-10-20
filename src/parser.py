"""HTML parsing and data normalization logic for catalog pages."""

import logging
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag

from src.models import BookItem

logger = logging.getLogger(__name__)

RATING_MAP: dict[str, int] = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

PRICE_PATTERN: re.Pattern[str] = re.compile(r"(\d+(?:\.\d+)?)")

STATUS_IN_STOCK: str = "In stock"
STATUS_OUT_OF_STOCK: str = "Out of stock"


def parse_price(raw_price: str) -> float:
    """Extract numeric price value as float from formatted currency string.

    Args:
        raw_price: Raw price text such as '£51.77'.

    Returns:
        Extracted price as a float.

    Raises:
        ValueError: If no numeric price pattern matches.
    """
    match = PRICE_PATTERN.search(raw_price)
    if not match:
        raise ValueError(f"Unable to parse price from string: '{raw_price}'")
    return float(match.group(1))


def parse_rating(classes: list[str]) -> int:
    """Extract integer rating from CSS class list.

    Args:
        classes: List of CSS classes from rating tag (e.g., ['star-rating', 'Three']).

    Returns:
        Integer rating between 1 and 5 (or 0 if unmapped).
    """
    for cls_name in classes:
        if cls_name in RATING_MAP:
            return RATING_MAP[cls_name]
    return 0


def parse_availability(raw_text: str) -> str:
    """Normalize catalog stock availability text.

    Args:
        raw_text: Text from availability paragraph.

    Returns:
        'In stock' or 'Out of stock'.
    """
    cleaned = raw_text.strip().lower()
    if "in stock" in cleaned:
        return STATUS_IN_STOCK
    return STATUS_OUT_OF_STOCK


def parse_book_pod(pod: Tag, page_url: str) -> BookItem | None:
    """Extract a single BookItem from an article.product_pod element.

    Args:
        pod: BeautifulSoup Tag representing the product container.
        page_url: The URL of the page containing this pod for resolving links.

    Returns:
        Validated BookItem or None if mandatory elements could not be parsed.
    """
    # Title extraction (prefer full 'title' attribute on link if available)
    title_link = pod.select_one("h3 > a")
    if not title_link:
        logger.warning("Skipping pod: missing title anchor tag")
        return None
    raw_title = title_link.get("title") or title_link.get_text()

    # Price extraction
    price_elem = pod.select_one("p.price_color")
    if not price_elem:
        logger.warning("Skipping pod '%s': missing price element", raw_title)
        return None
    try:
        price = parse_price(price_elem.get_text())
    except ValueError as exc:
        logger.warning("Skipping pod '%s': %s", raw_title, exc)
        return None

    # Rating extraction
    rating_elem = pod.select_one("p.star-rating")
    rating_classes = rating_elem.get("class", []) if rating_elem else []
    rating = parse_rating(rating_classes)
    if rating == 0:
        logger.warning("Missing or unknown rating for '%s', defaulting to 1", raw_title)
        rating = 1

    # Availability extraction
    avail_elem = pod.select_one("p.availability")
    avail_text = avail_elem.get_text() if avail_elem else ""
    availability = parse_availability(avail_text)

    # Image URL extraction
    img_elem = pod.select_one("img.thumbnail")
    relative_img_src = img_elem.get("src", "") if img_elem else ""
    image_url = urljoin(page_url, relative_img_src)

    return BookItem(
        title=raw_title,
        price=price,
        rating=rating,
        availability=availability,
        image_url=image_url,
    )


def extract_books(html: str, page_url: str) -> list[BookItem]:
    """Parse all valid book items from catalog page HTML.

    Args:
        html: Raw HTML content of catalog page.
        page_url: Base URL used to resolve relative URLs.

    Returns:
        List of parsed and validated BookItem instances.
    """
    soup = BeautifulSoup(html, "lxml")
    pods = soup.select("article.product_pod")
    books: list[BookItem] = []

    for pod in pods:
        item = parse_book_pod(pod, page_url)
        if item is not None:
            books.append(item)

    return books


def extract_next_page(html: str, current_url: str) -> str | None:
    """Find the next page URL if pagination link exists.

    Args:
        html: Raw HTML content of the page.
        current_url: Current page URL to resolve relative pagination links.

    Returns:
        Absolute URL of the next page, or None if last page.
    """
    soup = BeautifulSoup(html, "lxml")
    next_link = soup.select_one("li.next > a")
    if not next_link or not next_link.get("href"):
        return None

    relative_next = next_link["href"].strip()
    return urljoin(current_url, relative_next)
