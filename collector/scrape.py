"""Collect public Craigslist search listings. Extraction is not yet live-verified."""
import json
import os
import base64
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

def is_trailer_listing(title):
    """Require the advertised item itself to be a trailer or usable chassis."""
    text = str(title or "").lower()
    relevant = re.search(
        r"\b(trailers?|flat[ -]?beds?|car[ -]?haulers?|equipment[ -]?haulers?|"
        r"auto[ -]?transporters?|tow[ -]?doll(?:y|ies)|chassis|utility[ -]?haulers?|"
        r"hay[ -]?wagons?|camper[ -]?frames?|rv[ -]?frames?)\b", text
    )
    accessory = re.search(
        r"\btrailer (?:hitch|lights?|tires?|wheels?|axles?|parts?|brakes?|jack|"
        r"ramps?|fenders?|couplers?|locks?|wiring|accessories|park|home|rental|"
        r"repair|service)\b", text
    )
    return bool(relevant) and not bool(accessory)

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
        if title and is_trailer_listing(title) and price is not None and price <= MAX_PRICE:
            results.append({"title": title, "price": price, "location": location, "url": url})
    return results


def collect_ebay():
    """Use eBay's official Browse API when application credentials are configured."""
    client_id = os.environ.get("EBAY_CLIENT_ID", "")
    client_secret = os.environ.get("EBAY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print("eBay: awaiting EBAY_CLIENT_ID and EBAY_CLIENT_SECRET secrets; skipped.")
        return []
    try:
        auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        token_response = requests.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
            timeout=20,
        )
        token_response.raise_for_status()
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"}
        found = {}
        for term in ["utility trailer", "flatbed trailer", "car hauler trailer", "trailer chassis"]:
            response = requests.get(
                "https://api.ebay.com/buy/browse/v1/item_summary/search",
                headers=headers,
                params={"q": term, "limit": 50, "filter": "price:[50..1500],priceCurrency:USD"},
                timeout=25,
            )
            response.raise_for_status()
            for item in response.json().get("itemSummaries", []):
                title = item.get("title", "")
                url = item.get("itemWebUrl", "")
                price_data = item.get("price", {})
                try:
                    price = float(price_data.get("value", "nan"))
                except (TypeError, ValueError):
                    continue
                if not (is_trailer_listing(title) and url.startswith("https://www.ebay.com/") and 50 <= price <= MAX_PRICE):
                    continue
                place = item.get("itemLocation") or {}
                found[url] = {"title": title, "price": price, "location": ", ".join(filter(None, [place.get("city"), place.get("stateOrProvince")])), "city": place.get("stateOrProvince", ""), "url": url, "source": "eBay"}
            time.sleep(1)
        print(f"eBay: {len(found)} matching listings.")
        return list(found.values())
    except (requests.RequestException, KeyError, ValueError) as exc:
        print(f"eBay collection unavailable: {exc}")
        return []

def main():
    old = {}
    if DATA.exists():
        try:
            old = {item["url"]: item for item in json.loads(DATA.read_text(encoding="utf-8")) if item.get("url") and is_trailer_listing(item.get("title"))}
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
                    item["source"] = "Craigslist"
                    old[item["url"]] = item
                extracted += len(found)
            except requests.RequestException as exc:
                failures += 1
                print(f"Request failed: {city} / {term}: {exc}")
            time.sleep(2)
    for item in collect_ebay():
        now = datetime.now(timezone.utc).isoformat()
        item["last_seen"] = now
        item["first_seen"] = old.get(item["url"], {}).get("first_seen", now)
        old[item["url"]] = item
        extracted += 1
    if extracted == 0:
        print(f"No new listings extracted ({failures} request errors). Retaining previously verified trailer listings.")
        if not old:
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
