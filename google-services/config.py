from pathlib import Path

TOOL_DIR = Path.home() / "google-services"
CREDENTIALS_DIR = TOOL_DIR / "credentials"
CLIENT_SECRET_PATH = CREDENTIALS_DIR / "client_secret.json"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.readonly",
]
ALL_SCOPES = GMAIL_SCOPES + SHEETS_SCOPES
