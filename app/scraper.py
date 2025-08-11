# app/scraper.py
import requests
import pandas as pd

USER_AGENT = "tds-data-analyst-agent/1.0 (+https://example.com)"

def fetch_tables_from_url(url: str, timeout: int = 20):
    """
    Fetch page and return list of pandas DataFrames from HTML tables.
    """
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    tables = pd.read_html(resp.text)
    return tables