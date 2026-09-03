"""
Prefetch script - run this BEFORE your presentation, not during it.
------------------------------------------------------------------------
Pulls complaint narratives from the CFPB API once and saves them to a local
JSON file. The Streamlit app (app.py) will automatically use this cached
file instead of hitting the live CFPB API, so your demo loads instantly
and isn't at the mercy of a slow government server during your presentation.

Run this the night before (or morning of) your presentation:
    python prefetch_data.py
"""

import json
import requests

CFPB_API_URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
CACHE_FILE = "cached_complaints.json"

# Match these to what you'll actually select in the app during your demo.
PRODUCT = "Credit card"
SAMPLE_SIZE = 20


def fetch_complaints(product, size):
    params = {"product": product, "has_narrative": "true", "size": size}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    }
    response = requests.get(CFPB_API_URL, params=params, headers=headers, timeout=60)
    response.raise_for_status()
    hits = response.json()["hits"]["hits"]
    narratives = [hit["_source"]["complaint_what_happened"] for hit in hits]
    return [n for n in narratives if n]


def main():
    print(f"Fetching {SAMPLE_SIZE} complaints for '{PRODUCT}' from the live CFPB API...")
    print("(This may be slow - that's expected. This is the one time it's OK to wait.)")

    narratives = fetch_complaints(PRODUCT, SAMPLE_SIZE)

    cache = {"product": PRODUCT, "size": SAMPLE_SIZE, "narratives": narratives}
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

    print(f"Saved {len(narratives)} complaints to {CACHE_FILE}")
    print("Your Streamlit app will now load instantly from this file during your demo.")


if __name__ == "__main__":
    main()
