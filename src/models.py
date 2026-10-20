"""Data models and validation schemas for the bookstore scraper."""

from typing import Annotated
from pydantic import BaseModel, Field, field_validator


class BookItem(BaseModel):
    """Represents a normalized book record extracted from the catalog."""

    title: Annotated[str, Field(min_length=1, description="Book title stripped of excess whitespace")]
    price: Annotated[float, Field(ge=0.0, description="Product price in GBP as a numeric float")]
    rating: Annotated[int, Field(ge=1, le=5, description="Star rating integer from 1 to 5")]
    availability: Annotated[str, Field(description="Normalized stock status: 'In stock' or 'Out of stock'")]
    image_url: Annotated[str, Field(description="Fully-qualified absolute URL of the cover image")]

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        """Strip redundant whitespace from title."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Book title cannot be empty")
        return cleaned

    @field_validator("availability")
    @classmethod
    def validate_availability(cls, value: str) -> str:
        """Ensure availability is one of the expected normalized values."""
        normalized = value.strip()
        if normalized not in ("In stock", "Out of stock"):
            raise ValueError(f"Unexpected availability status: '{value}'")
        return normalized

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str) -> str:
        """Ensure image URL is absolute."""
        if not value.startswith("http://") and not value.startswith("https://"):
            raise ValueError(f"Image URL must be absolute (got '{value}')")
        return value


class ScraperConfig(BaseModel):
    """Runtime configuration schema for crawler execution."""

    start_url: str = "https://books.toscrape.com/catalogue/page-1.html"
    output_dir: str = "data/output"
    max_pages: int = 2
    delay_min: float = 1.0
    delay_max: float = 2.0
    timeout: int = 15
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )

    @field_validator("start_url")
    @classmethod
    def validate_start_url(cls, value: str) -> str:
        """Ensure starting URL uses standard HTTP/HTTPS schemes."""
        if not value.startswith("http://") and not value.startswith("https://"):
            raise ValueError(f"start_url must be an HTTP or HTTPS URL (got '{value}')")
        return value

    @field_validator("delay_max")
    @classmethod
    def validate_delays(cls, delay_max: float, info) -> float:
        """Ensure delay_max is at least delay_min."""
        delay_min = info.data.get("delay_min", 1.0)
        if delay_max < delay_min:
            raise ValueError("delay_max must be greater than or equal to delay_min")
        return delay_max
