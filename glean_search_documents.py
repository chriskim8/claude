#!/usr/bin/env python3
"""
Search Glean for documents edited by specific users in the last week.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode

def search_glean(query, username=None):
    """Search Glean for documents edited by a user."""

    # Glean instance URL
    GLEAN_INSTANCE = os.getenv("GLEAN_INSTANCE", "https://doximity-be.glean.com")
    GLEAN_API_KEY = os.getenv("GLEAN_API_KEY")

    if not GLEAN_API_KEY:
        print("Error: GLEAN_API_KEY environment variable not set")
        return None

    # Build search query with date filter for last 7 days
    today = datetime.now()
    one_week_ago = today - timedelta(days=7)
    date_filter = one_week_ago.strftime("%Y-%m-%d")

    # Construct search query
    if username:
        search_query = f'edited by:"{username}" OR author:"{username}"'
    else:
        search_query = query

    # API endpoint
    url = f"{GLEAN_INSTANCE}/api/v1/search"

    headers = {
        "Authorization": f"Bearer {GLEAN_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": search_query,
        "pageSize": 50,
        "filters": {
            "lastModifiedDate": {
                "from": date_filter
            }
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying Glean: {e}")
        return None

def format_results(results, user):
    """Format Glean search results."""
    if not results or "results" not in results:
        print(f"\nNo documents found for {user}")
        return

    print(f"\n{'='*80}")
    print(f"Documents edited by: {user}")
    print(f"{'='*80}")

    docs = results.get("results", [])
    if not docs:
        print(f"  No documents found in the last 7 days")
        return

    print(f"\n  Found {len(docs)} document(s):\n")

    for i, doc in enumerate(docs, 1):
        title = doc.get("title", "Unknown Title")
        doc_type = doc.get("docType", "Unknown Type")
        source = doc.get("source", {})
        source_type = source.get("displayName", "Unknown Source")
        url = doc.get("url", "No URL")
        last_modified = doc.get("lastModifiedDate", "Unknown")

        print(f"  {i}. {title}")
        print(f"     Type: {doc_type}")
        print(f"     Source: {source_type}")
        print(f"     Last Modified: {last_modified}")
        print(f"     URL: {url}")
        print()

def main():
    users = ["Aline Campbell", "Katrina Chaffin"]

    print("Searching Glean for documents edited in the last 7 days...\n")

    for user in users:
        results = search_glean("", username=user)
        format_results(results, user)

if __name__ == "__main__":
    main()
