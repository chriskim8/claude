from pathlib import Path

ZENDESK_DIR = Path.home() / "zendesk"
CREDENTIALS_DIR = ZENDESK_DIR / "credentials"

SUBDOMAIN_PATH = CREDENTIALS_DIR / "subdomain"
EMAIL_PATH = CREDENTIALS_DIR / "email"
API_TOKEN_PATH = CREDENTIALS_DIR / "api_token"
