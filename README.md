# BMW Approved Used Cars Scraper

Scrapy spider that scrapes used car listings from [BMW UK Approved Used Cars](https://usedcars.bmw.co.uk/) and stores them in a SQLite database.

Scrapes the first 5 pages of results. For each car, collects: `model`, `name`, `mileage`, `registered`, `engine`, `range_`, `exterior`, `fuel`, `transmission`, `registration`, `upholstery`.

## Setup & Run

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt

scrapy crawl bmw
```

Results are saved to `bmw_cars.db`. Duplicates are ignored by registration plate.
