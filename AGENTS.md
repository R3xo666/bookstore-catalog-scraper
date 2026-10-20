# AGENTS.md

## Project Overview
Production-grade, configuration-driven CLI web scraper and data normalization pipeline in Python targeting `books.toscrape.com`. Crawls catalog pages, normalizes product attributes, handles polite rate-limiting with exponential backoff session retries, tracks terminal progress with Rich, provides graceful shutdown on `SIGINT` (Ctrl+C), and exports clean datasets simultaneously to CSV and Excel (`.xlsx`).

## Tech Stack
- **Language:** Python 3.12+
- **Core Libraries:**
  - `requests` (HTTP session pooling & adapter retries)
  - `beautifulsoup4` + `lxml` (Fast HTML parsing)
  - `pydantic` v2 (Strict data models and field validation)
  - `pandas` + `openpyxl` (Dual CSV & Excel export)
  - `rich` (Terminal UI & progress reporting)
- **Testing:** `pytest` 8.x

## Code Conventions & Architecture
- **Directory Layout:**
  - `config/`: JSON configuration files (`config.json`).
  - `data/output/`: Target destination for exported datasets.
  - `src/`: Core logic modules.
    - `models.py`: Pydantic schema validation (`BookItem`, `ScraperConfig`).
    - `parser.py`: Pure parsing and normalization functions.
    - `crawler.py`: HTTP crawler with exponential backoff & delay jitter.
    - `exporter.py`: Dual CSV/Excel export with sanitization.
  - `tests/`: Offline pytest suite.
  - `main.py`: CLI entrypoint and signal handling.
- **Clean Code Standards:** Single Responsibility Principle (SRP), small functions (<20 lines), guard clauses, explicit type annotations on all functions, named constants.
- **Security Invariants:**
  - Sanitization of formula trigger characters (`=`, `+`, `-`, `@`) in CSV export to prevent spreadsheet injection.
  - Path traversal sanitization using base filename extraction.
  - Unsafe URL scheme rejection (only `http://` and `https://` permitted).
  - Maximum response size guard (10 MB) to prevent OOM/decompression bombs.

## Testing & Verification Requirements
- All new features and parsers must include unit tests in `tests/`.
- Run tests offline:
  ```bash
  .venv/bin/pytest -v tests/
  ```

## Build & Execution
- **Virtualenv Setup:**
  ```bash
  uv venv --python 3.12 .venv
  source .venv/bin/activate
  uv pip install -r requirements.txt
  ```
- **Run Scraper:**
  ```bash
  python3 main.py --pages 2 --output data/output --base-name sample_2pages
  ```
