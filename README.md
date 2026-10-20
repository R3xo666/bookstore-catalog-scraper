# Bookstore Catalog Scraper

A robust, production-grade command-line web scraper and data normalization pipeline built in Python. Designed to crawl e-commerce product catalogs (demo target: [books.toscrape.com](https://books.toscrape.com)), parse and normalize book details, handle pagination reliably, and export datasets simultaneously to CSV and Excel (`.xlsx`).

---

## Features

- **Strict Data Validation:** Powered by Pydantic models with sanitization for numeric prices, 1–5 integer star ratings, stock availability, and fully qualified image URLs.
- **Resilient HTTP Engine:** Built on `requests.Session` with automatic retry pooling (`urllib3.util.Retry`), exponential backoff on HTTP 429/5xx status codes, and custom User-Agent configuration.
- **Polite Crawling:** Configurable random delays (`delay_min` to `delay_max`) between requests to avoid IP bans and server throttling.
- **Dual Export:** Seamlessly writes UTF-8 CSV and Excel (`openpyxl`) files simultaneously with timestamps or customizable base names.
- **Interactive Terminal UI:** Rich progress bar displaying current status, page speed, elapsed time, and item count.
- **Graceful Shutdown (Signal Trapping):** Capturing `SIGINT` (`Ctrl+C`) automatically flushes accumulated items to disk, preventing data loss during early interruption.
- **Zero Hardcoding:** All parameters configurable via `config/config.json` and overridable via CLI arguments.

---

## Directory Layout

```
bookstore-scraper/
├── config/
│   └── config.json             # Runtime settings (delays, headers, limits, paths)
├── data/
│   └── output/                 # Destination for generated CSV/XLSX exports
│       ├── sample_2pages.csv   # Sample 2-page dataset
│       └── sample_2pages.xlsx  # Sample 2-page dataset
├── src/
│   ├── __init__.py
│   ├── models.py               # Pydantic data schemas and validation
│   ├── crawler.py              # HTTP session pooling, exponential retries & pagination
│   ├── parser.py               # HTML parsing, rating mapping & URL resolution
│   └── exporter.py             # Dual CSV & Excel writer with directory creation
├── tests/
│   ├── __init__.py
│   ├── test_parser.py          # Unit tests for parser and rating mapping
│   └── test_exporter.py        # Unit tests for CSV/Excel export
├── main.py                     # CLI entrypoint, argument parsing & Rich UI
├── requirements.txt            # Pinned production dependencies
└── README.md                   # Documentation and usage guide
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- `uv` (recommended) or standard `python3 -m venv`

### Option 1: Quickstart with `uv` (Fastest)
```bash
# Create virtual environment with Python 3.12
uv venv --python 3.12 .venv
source .venv/bin/activate

# Install pinned dependencies
uv pip install -r requirements.txt
```

### Option 2: Standard Virtualenv
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running the Scraper

### 1. Default Run (Crawls 2 pages as specified in config)
```bash
python3 main.py
```

### 2. Custom Page Limit
```bash
# Scrape exactly 5 pages
python3 main.py --pages 5

# Scrape entire catalog (all 50 pages)
python3 main.py --pages 0
```

### 3. Override Output Directory & Filename
```bash
python3 main.py --pages 2 --output data/output --base-name sample_2pages
```

### 4. Custom Starting URL
```bash
python3 main.py --url https://books.toscrape.com/catalogue/category/books/travel_2/index.html
```

---

## Command-Line Arguments

| Flag | Long Flag | Description | Default |
|------|-----------|-------------|---------|
| `-c` | `--config` | Path to JSON config file | `config/config.json` |
| `-u` | `--url` | Override starting URL | Set in config |
| `-p` | `--pages` | Override max pages (`0` for unlimited) | Set in config |
| `-o` | `--output` | Override export destination directory | `data/output` |
| `-b` | `--base-name` | Custom base filename without extension | `books_YYYYMMDD_HHMMSS` |

---

## Configuration Reference (`config/config.json`)

```json
{
  "start_url": "https://books.toscrape.com/catalogue/page-1.html",
  "output_dir": "data/output",
  "max_pages": 2,
  "delay_min": 1.0,
  "delay_max": 2.0,
  "timeout": 15,
  "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}
```

- `start_url`: The entry catalog URL.
- `output_dir`: Relative or absolute path where `.csv` and `.xlsx` files are saved.
- `max_pages`: Total number of pages to crawl before stopping. Set to `0` for infinite pagination.
- `delay_min` / `delay_max`: Polite crawling jitter window in seconds.
- `timeout`: Network socket timeout in seconds.
- `user_agent`: Custom HTTP User-Agent header string.

---

## Extracted Data Schema

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | `str` | Cleaned full title string | `"A Light in the Attic"` |
| `price` | `float` | Price in GBP without currency symbol | `51.77` |
| `rating` | `int` | Rating mapped from CSS words (1 to 5) | `3` |
| `availability` | `str` | Normalized status string | `"In stock"` |
| `image_url` | `str` | Fully resolved absolute cover URL | `"https://books.toscrape.com/media/cache/..."` |

---

## Running Unit Tests

Run the test suite offline without network access:
```bash
pytest -v tests/
```
