import csv
import io
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.schemas import (
    EmailRequest,
    BulkEmailRequest,
    ValidationResult,
    BulkValidationResult,
)
from app.config import MAX_BULK_EMAILS, MAX_UPLOAD_SIZE_BYTES, RATE_LIMIT_SINGLE, RATE_LIMIT_BULK
from app.validators.pipeline import validate_email_async, validate_bulk_async

logger = logging.getLogger("email_validator.api")
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post("/validate", response_model=ValidationResult)
@limiter.limit(RATE_LIMIT_SINGLE)
async def validate_single(request: Request, body: EmailRequest):
    """Validate a single email address."""
    logger.info("Validating: %s", body.email)
    try:
        result = await validate_email_async(body.email)
        logger.info("Result for %s: %s (score=%s)", body.email, result["verdict"], result["score"])
        return result
    except Exception:
        logger.exception("Validation failed for %s", body.email)
        raise HTTPException(status_code=500, detail="Validation failed unexpectedly")


@router.post("/validate/bulk", response_model=BulkValidationResult)
@limiter.limit(RATE_LIMIT_BULK)
async def validate_bulk(request: Request, body: BulkEmailRequest):
    """Validate multiple email addresses concurrently."""
    emails = list({e.strip() for e in body.emails if e.strip()})

    if len(emails) > MAX_BULK_EMAILS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_BULK_EMAILS} emails per request",
        )

    logger.info("Bulk validation: %d emails", len(emails))
    try:
        results = await validate_bulk_async(emails)
        response = _build_bulk_response(results)
        logger.info(
            "Bulk complete: %d total, %d valid, %d invalid",
            response["total"], response["valid"], response["invalid"],
        )
        return response
    except Exception:
        logger.exception("Bulk validation failed")
        raise HTTPException(status_code=500, detail="Bulk validation failed unexpectedly")


@router.post("/validate/bulk/upload", response_model=BulkValidationResult)
@limiter.limit(RATE_LIMIT_BULK)
async def validate_upload(request: Request, file: UploadFile = File(...)):
    """Validate emails from an uploaded CSV or TXT file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("csv", "txt"):
        raise HTTPException(status_code=400, detail="Only .csv and .txt files are accepted")

    content = await file.read()

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB",
        )

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")

    emails = _parse_emails_from_text(text, file.filename)

    if not emails:
        raise HTTPException(status_code=400, detail="No email addresses found in file")

    if len(emails) > MAX_BULK_EMAILS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_BULK_EMAILS} emails per request (found {len(emails)})",
        )

    logger.info("File upload: %s (%d bytes, %d emails)", file.filename, len(content), len(emails))
    try:
        results = await validate_bulk_async(emails)
        return _build_bulk_response(results)
    except Exception:
        logger.exception("File validation failed for %s", file.filename)
        raise HTTPException(status_code=500, detail="File validation failed unexpectedly")


def _parse_emails_from_text(text: str, filename: str) -> list[str]:
    """Extract email addresses from CSV or plain text."""
    emails: list[str] = []

    try:
        if filename.lower().endswith(".csv"):
            reader = csv.reader(io.StringIO(text))
            for row in reader:
                for cell in row:
                    cell = cell.strip()
                    if "@" in cell and len(cell) <= 320:
                        emails.append(cell)
        else:
            for line in text.splitlines():
                line = line.strip()
                if line and "@" in line:
                    for part in line.replace(";", ",").split(","):
                        part = part.strip()
                        if "@" in part and len(part) <= 320:
                            emails.append(part)
    except csv.Error:
        logger.warning("Malformed CSV in file %s", filename)

    return emails


def _build_bulk_response(results: list[dict]) -> dict:
    valid = sum(1 for r in results if r["verdict"] == "valid")
    invalid = sum(1 for r in results if r["verdict"] == "invalid")
    warnings = sum(1 for r in results if r["verdict"] == "warning")
    unknown = sum(1 for r in results if r["verdict"] == "unknown")

    return {
        "total": len(results),
        "valid": valid,
        "invalid": invalid,
        "warnings": warnings,
        "unknown": unknown,
        "results": results,
    }
