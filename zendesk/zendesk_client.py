"""Zendesk API client for Claude Code.

Provides authenticated access to the Zendesk API.
Credentials are read from ~/zendesk/credentials/.

Usage:
    from zendesk_client import zendesk_request

    tickets = zendesk_request("tickets.json")
    ticket  = zendesk_request("tickets/123.json")
    results = zendesk_request("search.json", params={"query": "status:open"})
"""

from __future__ import annotations

import requests

from config import SUBDOMAIN_PATH, EMAIL_PATH, API_TOKEN_PATH


def _get_credentials() -> tuple[str, str, str]:
    subdomain = SUBDOMAIN_PATH.read_text().strip()
    email = EMAIL_PATH.read_text().strip()
    token = API_TOKEN_PATH.read_text().strip()
    return subdomain, email, token


def zendesk_request(
    endpoint: str,
    method: str = "GET",
    params: dict | None = None,
    json: dict | None = None,
) -> dict:
    """Make an authenticated request to the Zendesk API.

    Args:
        endpoint: API endpoint, e.g. "tickets.json" or "search.json"
        method:   HTTP method (GET, POST, PUT, DELETE)
        params:   Query string parameters
        json:     JSON body for POST/PUT requests

    Returns:
        Parsed JSON response as a dict
    """
    subdomain, email, token = _get_credentials()
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    auth = (f"{email}/token", token)

    response = requests.request(
        method,
        f"{base_url}/{endpoint}",
        auth=auth,
        params=params,
        json=json,
    )
    response.raise_for_status()
    return response.json()
