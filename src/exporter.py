"""Dual CSV and Excel dataset exporter."""

from datetime import datetime
import logging
from pathlib import Path
from typing import Sequence
import pandas as pd

from src.models import BookItem

logger = logging.getLogger(__name__)

EXPORT_COLUMNS = ["title", "price", "rating", "availability", "image_url"]


DANGEROUS_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_for_spreadsheet(value: str) -> str:
    """Escape leading characters that could trigger formula execution in spreadsheets.

    Args:
        value: Input string value.

    Returns:
        Escaped string if prefix is hazardous, otherwise original string.
    """
    if isinstance(value, str) and value.startswith(DANGEROUS_FORMULA_PREFIXES):
        return f"'{value}"
    return value


def export_dataset(
    items: Sequence[BookItem],
    output_dir: str | Path,
    base_filename: str | None = None,
) -> tuple[Path, Path]:
    """Export collected book items simultaneously to CSV and Excel.

    Args:
        items: Sequence of BookItem objects.
        output_dir: Target directory path for exported files.
        base_filename: Optional base name without extension. If omitted,
            defaults to 'books_YYYYMMDD_HHMMSS'.

    Returns:
        Tuple of (csv_filepath, excel_filepath).
    """
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if not base_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_base_name = f"books_{timestamp}"
    else:
        # Sanitize to prevent path traversal (e.g. ../../evil)
        safe_base_name = Path(base_filename).name

    # Build DataFrame
    if items:
        records = [
            {
                k: sanitize_for_spreadsheet(v) if isinstance(v, str) else v
                for k, v in item.model_dump().items()
            }
            for item in items
        ]
        df = pd.DataFrame(records)[EXPORT_COLUMNS]
    else:
        df = pd.DataFrame(columns=EXPORT_COLUMNS)

    csv_path = target_dir / f"{safe_base_name}.csv"
    excel_path = target_dir / f"{safe_base_name}.xlsx"

    # Export CSV
    df.to_csv(csv_path, index=False, encoding="utf-8")
    logger.info("Saved CSV dataset to %s (%d records)", csv_path, len(df))

    # Export Excel using openpyxl engine
    df.to_excel(excel_path, index=False, engine="openpyxl")
    logger.info("Saved Excel dataset to %s (%d records)", excel_path, len(df))

    return csv_path, excel_path
