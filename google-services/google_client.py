"""Google Services client for Claude Code.

Provides authenticated access to Gmail, Google Sheets, and Google Drive.
Credentials are read from environment variables or local credential files.

On first run, opens a browser window for OAuth consent. After that,
credentials are cached and refreshed automatically.

Usage:
    from google_client import get_gmail_service, get_sheets_service, get_drive_service

    gmail = get_gmail_service()
    sheets = get_sheets_service()
    drive = get_drive_service()
"""

from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth import default
from googleapiclient.discovery import build

from config import CLIENT_SECRET_PATH, TOKEN_PATH, ALL_SCOPES


def _get_credentials() -> Credentials:
    """Get or refresh Google OAuth credentials.
    
    Priority:
    1. GOOGLE_APPLICATION_CREDENTIALS env var
    2. TOKEN_PATH (cached token)
    3. OAuth flow (interactive)
    """
    # Check for service account credentials (for cloud environments)
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        creds, _ = default(scopes=ALL_SCOPES)
        return creds
    
    # Load cached token if it exists
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), ALL_SCOPES)
        if not creds.expired:
            return creds
        if creds.refresh_token:
            creds.refresh(Request())
            return creds
    
    # Fall back to OAuth flow
    if not CLIENT_SECRET_PATH.exists():
        raise ValueError(
            f"CLIENT_SECRET_PATH not found at {CLIENT_SECRET_PATH}. "
            "Please ensure your client_secret.json is in ~/google-services/credentials/"
        )
    
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH),
        ALL_SCOPES
    )
    creds = flow.run_local_server(port=0)
    
    # Save credentials for next run
    with open(TOKEN_PATH, "w") as token_file:
        token_file.write(creds.to_json())
    
    return creds


def get_gmail_service():
    """Get Gmail API service."""
    creds = _get_credentials()
    return build("gmail", "v1", credentials=creds)


def get_sheets_service():
    """Get Google Sheets API service."""
    creds = _get_credentials()
    return build("sheets", "v4", credentials=creds)


def get_drive_service():
    """Get Google Drive API service."""
    creds = _get_credentials()
    return build("drive", "v3", credentials=creds)
