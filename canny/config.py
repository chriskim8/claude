from pathlib import Path

CANNY_DIR = Path.home() / "canny"
CREDENTIALS_DIR = CANNY_DIR / "credentials"
API_KEY_PATH = CREDENTIALS_DIR / "api_key"

BASE_URL = "https://canny.io/api/v1"
