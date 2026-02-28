import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Server
ALLOWED_ORIGINS: list[str] = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
).split(",")

# SMTP verification
SMTP_FROM_ADDRESS = os.getenv("SMTP_FROM_ADDRESS", "verify@emailvalidator.local")
SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", "10"))
DNS_TIMEOUT = int(os.getenv("DNS_TIMEOUT", "5"))

# Bulk processing
MAX_BULK_EMAILS = int(os.getenv("MAX_BULK_EMAILS", "5000"))
CONCURRENT_WORKERS = int(os.getenv("CONCURRENT_WORKERS", "50"))

# Rate limiting
RATE_LIMIT_SINGLE = os.getenv("RATE_LIMIT_SINGLE", "30/minute")
RATE_LIMIT_BULK = os.getenv("RATE_LIMIT_BULK", "5/minute")

# File upload
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(5 * 1024 * 1024)))  # 5MB

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
