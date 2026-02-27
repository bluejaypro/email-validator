import csv
import io

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.api.schemas import (
    EmailRequest,
    BulkEmailRequest,
    ValidationResult,
    BulkValidationResult,
)
from app.config import MAX_BULK_EMAILS
from app.validators.pipeline import validate_email

router = APIRouter()


@router.post("/validate", response_model=ValidationResult)
async def validate_single(request: EmailRequest):
    """Validate a single email address."""
    result = validate_email(request.email)
    return result


@router.post("/validate/bulk", response_model=BulkValidationResult)
async def validate_bulk(request: BulkEmailRequest):
    """Validate multiple email addresses."""
    emails = [e.strip() for e in request.emails if e.strip()]

    if len(emails) > MAX_BULK_EMAILS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_BULK_EMAILS} emails per request",
        )

    results = [validate_email(email) for email in emails]
    return _build_bulk_response(results)


@router.post("/validate/bulk/upload", response_model=BulkValidationResult)
async def validate_upload(file: UploadFile = File(...)):
    """Validate emails from an uploaded CSV or TXT file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
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
            detail=f"Maximum {MAX_BULK_EMAILS} emails per request",
        )

    results = [validate_email(email) for email in emails]
    return _build_bulk_response(results)


def _parse_emails_from_text(text: str, filename: str) -> list[str]:
    """Extract email addresses from CSV or plain text."""
    emails = []

    if filename.lower().endswith(".csv"):
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            for cell in row:
                cell = cell.strip()
                if "@" in cell:
                    emails.append(cell)
    else:
        for line in text.splitlines():
            line = line.strip()
            if line and "@" in line:
                # Handle comma or semicolon separated emails in a line
                for part in line.replace(";", ",").split(","):
                    part = part.strip()
                    if "@" in part:
                        emails.append(part)

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
