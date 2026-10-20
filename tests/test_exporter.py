"""Unit tests for CSV and Excel dataset exporter."""

from pathlib import Path
import pandas as pd
import pytest

from src.exporter import export_dataset
from src.models import BookItem


@pytest.fixture
def sample_books() -> list[BookItem]:
    return [
        BookItem(
            title="Book Alpha",
            price=19.99,
            rating=5,
            availability="In stock",
            image_url="https://books.toscrape.com/media/alpha.jpg",
        ),
        BookItem(
            title="Book Beta",
            price=42.50,
            rating=2,
            availability="In stock",
            image_url="https://books.toscrape.com/media/beta.jpg",
        ),
    ]


def test_export_dataset_creates_files(tmp_path: Path, sample_books: list[BookItem]) -> None:
    csv_file, excel_file = export_dataset(
        items=sample_books,
        output_dir=tmp_path,
        base_filename="test_books",
    )

    assert csv_file.exists()
    assert excel_file.exists()
    assert csv_file.name == "test_books.csv"
    assert excel_file.name == "test_books.xlsx"

    # Verify CSV format and data
    df_csv = pd.read_csv(csv_file)
    assert len(df_csv) == 2
    assert list(df_csv.columns) == ["title", "price", "rating", "availability", "image_url"]
    assert df_csv.loc[0, "title"] == "Book Alpha"
    assert float(df_csv.loc[0, "price"]) == 19.99
    assert int(df_csv.loc[0, "rating"]) == 5
    assert df_csv.loc[0, "availability"] == "In stock"

    # Verify Excel format and data
    df_excel = pd.read_excel(excel_file, engine="openpyxl")
    assert len(df_excel) == 2
    assert df_excel.loc[1, "title"] == "Book Beta"
    assert float(df_excel.loc[1, "price"]) == 42.50
    assert int(df_excel.loc[1, "rating"]) == 2


def test_export_dataset_empty(tmp_path: Path) -> None:
    csv_file, excel_file = export_dataset(
        items=[],
        output_dir=tmp_path,
        base_filename="empty_books",
    )

    assert csv_file.exists()
    assert excel_file.exists()

    df_csv = pd.read_csv(csv_file)
    assert len(df_csv) == 0
    assert list(df_csv.columns) == ["title", "price", "rating", "availability", "image_url"]


def test_export_formula_injection_escaping(tmp_path: Path) -> None:
    malicious_item = BookItem(
        title="=SUM(A1:A10)",
        price=10.0,
        rating=3,
        availability="In stock",
        image_url="https://books.toscrape.com/malicious.jpg",
    )
    csv_file, _ = export_dataset([malicious_item], output_dir=tmp_path, base_filename="sec_test")
    df_csv = pd.read_csv(csv_file)
    # Ensure leading '=' was escaped with a single quote
    assert df_csv.loc[0, "title"] == "'=SUM(A1:A10)"


def test_export_path_traversal_sanitization(tmp_path: Path) -> None:
    item = BookItem(
        title="Safe Book",
        price=10.0,
        rating=3,
        availability="In stock",
        image_url="https://books.toscrape.com/book.jpg",
    )
    csv_file, excel_file = export_dataset(
        [item],
        output_dir=tmp_path,
        base_filename="../../malicious_escape",
    )
    # The file should be saved strictly inside tmp_path under basename
    assert csv_file.parent.resolve() == tmp_path.resolve()
    assert csv_file.name == "malicious_escape.csv"

