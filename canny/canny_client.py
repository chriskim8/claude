"""Canny API client for Claude Code.

Provides authenticated access to the Canny API.
API key is read from CANNY_API_KEY environment variable.

Usage:
    from canny_client import canny_request

    boards = canny_request("boards/list")
    posts = canny_request("posts/list", {"boardID": "..."})
"""

from __future__ import annotations

import os
import requests

from config import BASE_URL


def _get_api_key() -> str:
    """Read API key from environment variable or credentials file.
    
    Priority:
    1. CANNY_API_KEY environment variable (for Claude Code)
    2. ~/canny/credentials/api_key file (for local development)
    """
    # Try environment variable first (Claude Code)
    api_key = os.environ.get("CANNY_API_KEY")
    if api_key:
        return api_key.strip()
    
    # Fall back to file (local development)
    try:
        from config import API_KEY_PATH
        return API_KEY_PATH.read_text().strip()
    except Exception as e:
        raise ValueError(
            "CANNY_API_KEY not set. Please set the CANNY_API_KEY environment variable "
            "or ensure ~/canny/credentials/api_key exists."
        ) from e


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
