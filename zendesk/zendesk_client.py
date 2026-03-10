"""Zendesk API client for Claude Code.

Provides authenticated access to the Zendesk API.
Credentials are read from environment variables.

Usage:
    from zendesk_client import zendesk_request

    tickets = zendesk_request("tickets.json")
    ticket  = zendesk_request("tickets/123.json")
    results = zendesk_request("search.json", params={"query": "status:open"})
"""

from __future__ import annotations

import os
import requests


def _get_credentials() -> tuple[str, str, str]:
    """Get Zendesk credentials from environment variables or files.
    
    Priority:
    1. Environment variables (for Claude Code)
    2. Credential files (for local development)
    """
    # Try environment variables first
    subdomain = os.environ.get("ZENDESK_SUBDOMAIN")
    email = os.environ.get("ZENDESK_EMAIL")
    token = os.environ.get("ZENDESK_API_TOKEN")
    
    if subdomain and email and token:
        return subdomain, email, token
    
    # Fall back to files (local development)
    try:
        from config import SUBDOMAIN_PATH, EMAIL_PATH, API_TOKEN_PATH
        subdomain = subdomain or SUBDOMAIN_PATH.read_text().strip()
        email = email or EMAIL_PATH.read_text().strip()
        token = token or API_TOKEN_PATH.read_text().strip()
        return subdomain, email, token
    except Exception as e:
        raise ValueError(
            "Zendesk credentials not set. Please set ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, "
            "and ZENDESK_API_TOKEN environment variables or ensure credential files exist."
        ) from e


def zendesk_request(
    endpoint: str,
    method: str = "GET",
    params: dict | None = None,
    json_data: dict | None = None,
) -> dict | list:
    """Make an authenticated request to the Zendesk API.

    Args:
        endpoint: API endpoint path (e.g. "tickets.json")
        method: HTTP method (GET, POST, PUT, DELETE)
        params: Query parameters
        json_data: JSON body data

    Returns:
        Parsed JSON response
    """
    subdomain, email, token = _get_credentials()
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    url = f"{base_url}/{endpoint}"

    auth = (f"{email}/token", token)
    
    response = requests.request(
        method=method,
        url=url,
        params=params,
        json=json_data,
        auth=auth,
    )
    response.raise_for_status()
    return response.json()
