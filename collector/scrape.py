"""Collect public Craigslist search listings. Extraction is not yet live-verified."""
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CITIES = ["charleston", "columbia", "hiltonhead", "myrtlebeach", "augusta", "savannah"]
TERMS = ["8.5x16 trailer", "8 x 16 trailer", "8.5 x 16 flatbed", "16 ft utility trailer", "16 foot car hauler"]
MAX_PRICE = 1500
DATA = ROOT / "data" / "listings.json"
HEADERS = {"User-Agent": "TrailerHunt/1.0 (personal research; GitHub JadesTheDev/Trailer-Hunt)"}

def parse_price(value):
    match = re.search(r"\$?\s*([\d,]+)", str(value or ""))
    return int(match.group(1).replace(",", "")) if match else None

def parse_page(html, base):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for node in soup.select("li.cl-static-search-result, li.cl-search-result, li.result-row"):
        link = node.select_one("a[href]")
        if link is None:
            continue
        url = urljoin(base, link.get("href", ""))
        parsed = urlparse(url)
        if parsed.scheme != "https" or not (parsed.hostname or "").endswith(".craigslist.org"):
            continue
        title_node = node.select_one(".title, .cl-app-title, .result-title, h3")
        title = title_node.get_text(" ", strip=True) if title_node else link.get_text(" ", strip=True)
        price_node = node.select_one(".price, .result-price")
        price = parse_price(price_node.get_text(" ", strip=True) if price_node else "")
        location_node = node.select_one(".location, .result-hood")
        location = location_node.get_text(" ", strip=True) if location_node else ""
        if title and price is not None and price <= MAX_PRICE:
            results.append({"title": title, "price": price, "location": location, "url": url})
    return results

def main():
    old = {}
    if DATA.exists():
        try:
            old = {item["url"]: item for item in json.loads(DATA.read_text(encoding="utf-8")) if item.get("url")}
        except (ValueError, TypeError, KeyError):
            print("Invalid existing data: stopping without overwriting it.")
            return
    extracted = 0
    failures = 0
    for city in CITIES:
        for term in TERMS:
            base = f"https://{city}.craigslist.org/search/sss"
            try:
                response = requests.get(base, params={"query": term, "max_price": MAX_PRICE}, headers=HEADERS, timeout=20)
                response.raise_for_status()
                found = parse_page(response.text, response.url)
                print(f"{city} / {term}: {len(found)} extracted")
                now = datetime.now(timezone.utc).isoformat()
                for item in found:
                    item["city"] = city
                    item["last_seen"] = now
                    item["first_seen"] = old.get(item["url"], {}).get("first_seen", now)
                    old[item["url"]] = item
                extracted += len(found)
            except requests.RequestException as exc:
                failures += 1
                print(f"Request failed: {city} / {term}: {exc}")
            time.sleep(2)
    if extracted == 0:
        print(f"No listings extracted ({failures} request errors). Keeping previous data; check access and HTML.")
        return
    payload = json.dumps(sorted(old.values(), key=lambda x: x["last_seen"], reverse=True), indent=2) + "\n"
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(payload, encoding="utf-8")
    published = ROOT / "docs" / "data" / "listings.json"
    published.parent.mkdir(parents=True, exist_ok=True)
    published.write_text(payload, encoding="utf-8")
    print(f"Saved {len(old)} unique listings.")

if __name__ == "__main__":
    main()
