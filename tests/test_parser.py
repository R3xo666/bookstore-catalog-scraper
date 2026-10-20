"""Unit tests for HTML parser and normalizer."""

import pytest
from src.parser import (
    extract_books,
    extract_next_page,
    parse_availability,
    parse_price,
    parse_rating,
)

SAMPLE_CATALOG_HTML = """
<!DOCTYPE html>
<html>
<body>
<ol class="row">
    <li class="col-xs-6 col-sm-4 col-md-3 col-lg-3">
        <article class="product_pod">
            <div class="image_container">
                <a href="catalogue/a-light-in-the-attic_1000/index.html">
                    <img src="../media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg" alt="A Light in the Attic" class="thumbnail">
                </a>
            </div>
            <p class="star-rating Three">
                <i class="icon-star"></i>
                <i class="icon-star"></i>
                <i class="icon-star"></i>
            </p>
            <h3><a href="catalogue/a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in the ...</a></h3>
            <div class="product_price">
                <p class="price_color">£51.77</p>
                <p class="instock availability">
                    <i class="icon-ok"></i>
                    In stock
                </p>
            </div>
        </article>
    </li>
    <li class="col-xs-6 col-sm-4 col-md-3 col-lg-3">
        <article class="product_pod">
            <div class="image_container">
                <a href="catalogue/tipping-the-velvet_999/index.html">
                    <img src="../media/cache/26/0c/260c6ae16bce31c8f8c95daddd9f4a1c.jpg" alt="Tipping the Velvet" class="thumbnail">
                </a>
            </div>
            <p class="star-rating One">
                <i class="icon-star"></i>
            </p>
            <h3><a href="catalogue/tipping-the-velvet_999/index.html" title="Tipping the Velvet">Tipping the Velvet</a></h3>
            <div class="product_price">
                <p class="price_color">£53.74</p>
                <p class="instock availability">
                    <i class="icon-ok"></i>
                    In stock
                </p>
            </div>
        </article>
    </li>
</ol>
<ul class="pager">
    <li class="current">Page 1 of 50</li>
    <li class="next"><a href="page-2.html">next</a></li>
</ul>
</body>
</html>
"""


def test_parse_price_valid() -> None:
    assert parse_price("£51.77") == 51.77
    assert parse_price("$19.99") == 19.99
    assert parse_price("0.99") == 0.99
    assert parse_price("100") == 100.0


def test_parse_price_invalid() -> None:
    with pytest.raises(ValueError, match="Unable to parse price"):
        parse_price("No price available")


@pytest.mark.parametrize(
    "classes,expected",
    [
        (["star-rating", "One"], 1),
        (["star-rating", "Two"], 2),
        (["star-rating", "Three"], 3),
        (["star-rating", "Four"], 4),
        (["star-rating", "Five"], 5),
        (["star-rating", "Unknown"], 0),
        ([], 0),
    ],
)
def test_parse_rating(classes: list[str], expected: int) -> None:
    assert parse_rating(classes) == expected


def test_parse_availability() -> None:
    assert parse_availability("\n    In stock\n") == "In stock"
    assert parse_availability("In stock (22 available)") == "In stock"
    assert parse_availability("Out of stock") == "Out of stock"
    assert parse_availability("Sold out") == "Out of stock"


def test_extract_books() -> None:
    base_url = "https://books.toscrape.com/catalogue/page-1.html"
    books = extract_books(SAMPLE_CATALOG_HTML, base_url)

    assert len(books) == 2

    book1 = books[0]
    assert book1.title == "A Light in the Attic"
    assert book1.price == 51.77
    assert book1.rating == 3
    assert book1.availability == "In stock"
    assert book1.image_url.startswith("https://books.toscrape.com/")
    assert "2cdad67c44b002e7ead0cc35693c0e8b.jpg" in book1.image_url

    book2 = books[1]
    assert book2.title == "Tipping the Velvet"
    assert book2.price == 53.74
    assert book2.rating == 1
    assert book2.availability == "In stock"


def test_extract_next_page() -> None:
    current_url = "https://books.toscrape.com/catalogue/page-1.html"
    next_url = extract_next_page(SAMPLE_CATALOG_HTML, current_url)
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_extract_next_page_none() -> None:
    html_without_next = "<html><body><ul class='pager'><li>Page 50 of 50</li></ul></body></html>"
    assert extract_next_page(html_without_next, "https://books.toscrape.com/") is None
