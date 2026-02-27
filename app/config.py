from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

SMTP_FROM_ADDRESS = "verify@emailvalidator.local"
SMTP_TIMEOUT = 10
DNS_TIMEOUT = 5
MAX_BULK_EMAILS = 500
