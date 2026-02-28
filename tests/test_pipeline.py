import asyncio
from unittest.mock import patch, AsyncMock
from app.validators.pipeline import validate_email, validate_email_async, validate_bulk_async


_domain_ok = {"name": "domain", "label": "Domain Check", "passed": True, "message": "ok"}
_mx_ok = {"name": "mx", "label": "MX Record", "passed": True, "message": "ok"}
_smtp_ok = {"name": "smtp", "label": "SMTP Verification", "passed": True, "message": "ok"}
_smtp_none = {"name": "smtp", "label": "SMTP Verification", "passed": None, "message": "timeout"}
_smtp_fail = {"name": "smtp", "label": "SMTP Verification", "passed": False, "message": "no"}


# --- Sync pipeline ---

def test_invalid_syntax():
    result = validate_email("not-an-email")
    assert result["verdict"] == "invalid"
    assert result["score"] == 0.0
    assert len(result["checks"]) == 1
    assert result["checks"][0]["name"] == "syntax"


def test_empty_email():
    result = validate_email("")
    assert result["verdict"] == "invalid"
    assert result["is_valid"] is False


@patch("app.validators.pipeline.check_smtp")
@patch("app.validators.pipeline.check_mx")
@patch("app.validators.pipeline.check_domain")
def test_valid_email(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = _domain_ok
    mock_mx.return_value = _mx_ok
    mock_smtp.return_value = _smtp_ok

    result = validate_email("user@gmail.com")
    assert result["verdict"] == "valid"
    assert result["score"] == 1.0
    assert result["is_valid"] is True


@patch("app.validators.pipeline.check_smtp")
@patch("app.validators.pipeline.check_mx")
@patch("app.validators.pipeline.check_domain")
def test_disposable_email(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = _domain_ok
    mock_mx.return_value = _mx_ok
    mock_smtp.return_value = _smtp_ok

    result = validate_email("test@mailinator.com")
    assert result["verdict"] == "warning"
    assert result["score"] == 0.4


@patch("app.validators.pipeline.check_smtp")
@patch("app.validators.pipeline.check_mx")
@patch("app.validators.pipeline.check_domain")
def test_domain_typo(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = {
        "name": "domain", "label": "Domain Check",
        "passed": False, "message": "Possible typo", "suggestion": "user@gmail.com"
    }
    result = validate_email("user@gmial.com")
    assert result["verdict"] == "warning"
    assert result["suggestion"] == "user@gmail.com"


@patch("app.validators.pipeline.check_smtp")
@patch("app.validators.pipeline.check_mx")
@patch("app.validators.pipeline.check_domain")
def test_mx_failure(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = _domain_ok
    mock_mx.return_value = {"name": "mx", "label": "MX Record", "passed": False, "message": "no MX"}
    result = validate_email("user@example.com")
    assert result["verdict"] == "invalid"
    assert result["score"] == 0.1


@patch("app.validators.pipeline.check_smtp")
@patch("app.validators.pipeline.check_mx")
@patch("app.validators.pipeline.check_domain")
def test_smtp_inconclusive(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = _domain_ok
    mock_mx.return_value = _mx_ok
    mock_smtp.return_value = _smtp_none
    result = validate_email("user@example.com")
    assert result["verdict"] == "unknown"
    assert result["score"] == 0.6


@patch("app.validators.pipeline.check_smtp")
@patch("app.validators.pipeline.check_mx")
@patch("app.validators.pipeline.check_domain")
def test_smtp_fail(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = _domain_ok
    mock_mx.return_value = _mx_ok
    mock_smtp.return_value = _smtp_fail
    result = validate_email("user@example.com")
    assert result["verdict"] == "invalid"
    assert result["score"] == 0.2


@patch("app.validators.pipeline.check_smtp")
@patch("app.validators.pipeline.check_mx")
@patch("app.validators.pipeline.check_domain")
def test_role_based_with_smtp_pass(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = _domain_ok
    mock_mx.return_value = _mx_ok
    mock_smtp.return_value = _smtp_ok
    result = validate_email("admin@example.com")
    assert result["verdict"] == "warning"
    assert result["score"] == 0.7


@patch("app.validators.pipeline.check_smtp")
@patch("app.validators.pipeline.check_mx")
@patch("app.validators.pipeline.check_domain")
def test_result_structure(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = _domain_ok
    mock_mx.return_value = _mx_ok
    mock_smtp.return_value = _smtp_ok
    result = validate_email("user@example.com")
    assert "email" in result
    assert "is_valid" in result
    assert "score" in result
    assert "verdict" in result
    assert "checks" in result
    assert isinstance(result["checks"], list)
    assert len(result["checks"]) == 6


# --- Async pipeline ---

@patch("app.validators.pipeline.check_smtp_async", new_callable=AsyncMock)
@patch("app.validators.pipeline.check_mx_async", new_callable=AsyncMock)
@patch("app.validators.pipeline.check_domain_async", new_callable=AsyncMock)
def test_validate_email_async(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = _domain_ok
    mock_mx.return_value = _mx_ok
    mock_smtp.return_value = _smtp_ok
    result = asyncio.get_event_loop().run_until_complete(validate_email_async("user@gmail.com"))
    assert result["verdict"] == "valid"
    assert result["is_valid"] is True


def test_validate_email_async_invalid_syntax():
    result = asyncio.get_event_loop().run_until_complete(validate_email_async("bad-email"))
    assert result["verdict"] == "invalid"
    assert result["score"] == 0.0


@patch("app.validators.pipeline.check_smtp_async", new_callable=AsyncMock)
@patch("app.validators.pipeline.check_mx_async", new_callable=AsyncMock)
@patch("app.validators.pipeline.check_domain_async", new_callable=AsyncMock)
def test_validate_bulk_async(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = _domain_ok
    mock_mx.return_value = _mx_ok
    mock_smtp.return_value = _smtp_ok
    emails = ["user1@gmail.com", "user2@gmail.com", "bad-email"]
    results = asyncio.get_event_loop().run_until_complete(validate_bulk_async(emails))
    assert len(results) == 3
    valid_count = sum(1 for r in results if r["verdict"] == "valid")
    invalid_count = sum(1 for r in results if r["verdict"] == "invalid")
    assert valid_count == 2
    assert invalid_count == 1


@patch("app.validators.pipeline.check_smtp_async", new_callable=AsyncMock)
@patch("app.validators.pipeline.check_mx_async", new_callable=AsyncMock)
@patch("app.validators.pipeline.check_domain_async", new_callable=AsyncMock)
def test_bulk_deduplication_in_results(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = _domain_ok
    mock_mx.return_value = _mx_ok
    mock_smtp.return_value = _smtp_ok
    emails = ["user@gmail.com", "user@gmail.com", "other@gmail.com"]
    results = asyncio.get_event_loop().run_until_complete(validate_bulk_async(emails))
    assert len(results) == 3
