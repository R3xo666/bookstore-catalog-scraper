"""Unit test for graceful interruption and signal handling."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from main import ScraperApp
from src.models import BookItem, ScraperConfig


def test_interruption_flushes_accumulated_items(tmp_path: Path) -> None:
    config = ScraperConfig(output_dir=str(tmp_path), max_pages=5)
    app = ScraperApp(config=config, base_name="interrupted_run")

    # Simulate accumulated items before signal
    app.accumulated_items = [
        BookItem(
            title="Partial Book 1",
            price=15.00,
            rating=4,
            availability="In stock",
            image_url="https://books.toscrape.com/media/part1.jpg",
        ),
        BookItem(
            title="Partial Book 2",
            price=25.50,
            rating=5,
            availability="In stock",
            image_url="https://books.toscrape.com/media/part2.jpg",
        ),
    ]

    # Trigger signal handler and assert sys.exit(0) is called
    with pytest.raises(SystemExit) as exc_info:
        app._handle_signal(signum=2, _frame=None)

    assert exc_info.value.code == 0
    assert (tmp_path / "interrupted_run.csv").exists()
    assert (tmp_path / "interrupted_run.xlsx").exists()
