# TOI ePaper Scraper

Python scraper to automatically download the **Times of India Delhi edition** PDF daily.

## How it works

1. Hits `dailyepaper.in` and scrapes the latest Delhi edition link
2. Extracts the Google Drive file ID from the page
3. Downloads the PDF with automatic confirmation page handling
4. Saves to `~/Documents/newspapers/toi/` with date-stamped filename

## Usage

```bash
pip install requests beautifulsoup4
python3 scraper.py
```

Output: `TOI_Delhi_YYYY-MM-DD.pdf` in your newspapers folder.

## Automate with cron

```bash
# Run daily at 7 AM
0 7 * * * /usr/bin/python3 /path/to/scraper.py >> /var/log/toi-scraper.log 2>&1
```

## Stack

`Python` `BeautifulSoup` `Requests` `Web Scraping`
