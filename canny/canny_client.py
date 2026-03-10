"""Canny API client for Claude Code.

Provides authenticated access to the Canny API.
API key is read from ~/canny/credentials/api_key.

Usage:
    from canny_client import canny_request

    boards = canny_request("boards/list")
    posts = canny_request("posts/list", {"boardID": "..."})
"""

from __future__ import annotations

import requests

from config import API_KEY_PATH, BASE_URL


def _get_api_key() -> str:
    """Read API key from credentials file."""
    return API_KEY_PATH.read_text().strip()


def canny_request(endpoint: str, params: dict | None = None) -> dict:
    """Make an authenticated POST request to the Canny API.

    Args:
        endpoint: API endpoint path, e.g. "boards/list" or "posts/retrieve"
        params: Optional dict of additional parameters

    Returns:
        Parsed JSON response as a dict
    """
    data = {"apiKey": _get_api_key()}
    if params:
        data.update(params)
    response = requests.post(f"{BASE_URL}/{endpoint}", data=data)
    response.raise_for_status()
    return response.json()
