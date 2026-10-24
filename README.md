# BookPulse

BookPulse is a Python command-line scraper for the sample catalogue at [books.toscrape.com](https://books.toscrape.com). It follows catalogue pages, validates each record, and exports the results as CSV and Excel files.

## What it collects

Each record contains the book title, price, rating, availability, and cover image URL. The parser normalizes the catalogue’s price and rating formats. Requests use a configurable delay, and the crawler retries transient HTTP failures.

## Setup

Python 3.10 or newer is recommended.

~~~bash
git clone https://github.com/R3xo666/bookstore-catalog-scraper.git
cd bookstore-catalog-scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
~~~

## Run

The default configuration reads two pages from books.toscrape.com and writes files under `data/output/`.

~~~bash
python3 main.py
~~~

Set a page limit and output name from the command line:

~~~bash
python3 main.py --pages 5 --output data/output --base-name sample
~~~

`--pages 0` follows pages until the catalogue has no next page. Use `--config` to select a JSON configuration file; `--url` can override its starting URL.

## Output

The scraper writes matching `.csv` and `.xlsx` files. The default filename includes the run timestamp. Leading spreadsheet formula characters in text fields are escaped before export.

## Tests

~~~bash
pytest -v
~~~