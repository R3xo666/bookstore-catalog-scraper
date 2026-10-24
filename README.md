# BookPulse

BookPulse is a Python command-line scraper for the sample catalogue at [books.toscrape.com](https://books.toscrape.com). It follows catalogue pagination, validates each book record, and exports the results to CSV and Excel.

## What it collects

Each record contains:

- `title`
- `price` as a number
- `rating` from 1 to 5
- `availability`
- `image_url` as an absolute URL

The parser normalizes the catalogue’s price, rating, and availability text. Requests use the configured timeout and a randomized delay. Transient responses such as HTTP 429 and 5xx are retried. A response larger than 10 MB is rejected. Text written to the spreadsheets is escaped when it begins with a spreadsheet formula character.

## Requirements and setup

Python 3.10 or newer is recommended.

~~~bash
git clone https://github.com/R3xo666/bookstore-catalog-scraper.git
cd bookstore-catalog-scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
~~~

## Run

The default configuration reads two pages from Books to Scrape and writes output under `data/output/`.

~~~bash
python3 main.py
~~~

For example, read five pages and choose the output filename:

~~~bash
python3 main.py --pages 5 --output data/output --base-name sample
~~~

Set `--pages 0` to continue until the next-page link is absent.

### Command-line options

| Option | Description | Default |
| --- | --- | --- |
| `-c`, `--config` | JSON configuration file | `config/config.json` |
| `-u`, `--url` | Starting page URL | Value from config |
| `-p`, `--pages` | Maximum pages; `0` means follow pagination to the end | Value from config |
| `-o`, `--output` | Output directory | `data/output` |
| `-b`, `--base-name` | Output filename without an extension | Timestamped `books_...` name |

### Configuration

`config/config.json` sets `start_url`, `output_dir`, `max_pages`, `delay_min`, `delay_max`, `timeout`, and `user_agent`. The checked-in settings start at the first Books to Scrape catalogue page, allow two pages, wait 1–2 seconds between requests, and use a 15-second timeout. Command-line options override the URL, page limit, and output directory.

## Output

Each run writes matching `.csv` and `.xlsx` files. If `--base-name` is omitted, the filename includes the run timestamp.

## Tests

~~~bash
pytest -v
~~~