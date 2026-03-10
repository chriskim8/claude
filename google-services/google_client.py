"""Google API client for Claude Code.

Provides authenticated access to Gmail, Google Sheets, and Google Drive.
On first run, opens a browser window for OAuth consent. After that,
credentials are cached and refreshed automatically.
"""

from __future__ import annotations

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CLIENT_SECRET_PATH, TOKEN_PATH, ALL_SCOPES


def _get_credentials() -> Credentials:
    """Get or refresh Google OAuth credentials."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), ALL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_PATH), ALL_SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds


def get_gmail_service():
    """Build and return the Gmail API service."""
    return build("gmail", "v1", credentials=_get_credentials())


def get_sheets_service():
    """Build and return the Google Sheets API service."""
    return build("sheets", "v4", credentials=_get_credentials())


def get_drive_service():
    """Build and return the Google Drive API service."""
    return build("drive", "v3", credentials=_get_credentials())
