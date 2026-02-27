import asyncio
from unittest.mock import patch, AsyncMock
from app.validators.pipeline import validate_email, validate_email_async, validate_bulk_async


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
    mock_domain.return_value = {"name": "domain", "label": "Domain Check", "passed": True, "message": "ok"}
    mock_mx.return_value = {"name": "mx", "label": "MX Record", "passed": True, "message": "ok"}
    mock_smtp.return_value = {"name": "smtp", "label": "SMTP Verification", "passed": True, "message": "ok"}

    result = validate_email("user@gmail.com")
    assert result["verdict"] == "valid"
    assert result["score"] == 1.0
    assert result["is_valid"] is True


@patch("app.validators.pipeline.check_smtp")
@patch("app.validators.pipeline.check_mx")
@patch("app.validators.pipeline.check_domain")
def test_disposable_email(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = {"name": "domain", "label": "Domain Check", "passed": True, "message": "ok"}
    mock_mx.return_value = {"name": "mx", "label": "MX Record", "passed": True, "message": "ok"}
    mock_smtp.return_value = {"name": "smtp", "label": "SMTP Verification", "passed": True, "message": "ok"}

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
def test_result_structure(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = {"name": "domain", "label": "Domain Check", "passed": True, "message": "ok"}
    mock_mx.return_value = {"name": "mx", "label": "MX Record", "passed": True, "message": "ok"}
    mock_smtp.return_value = {"name": "smtp", "label": "SMTP Verification", "passed": True, "message": "ok"}

    result = validate_email("user@example.com")
    assert "email" in result
    assert "is_valid" in result
    assert "score" in result
    assert "verdict" in result
    assert "checks" in result
    assert isinstance(result["checks"], list)


# ---- Async pipeline tests ----

@patch("app.validators.pipeline.check_smtp_async", new_callable=AsyncMock)
@patch("app.validators.pipeline.check_mx_async", new_callable=AsyncMock)
@patch("app.validators.pipeline.check_domain_async", new_callable=AsyncMock)
def test_validate_email_async(mock_domain, mock_mx, mock_smtp):
    mock_domain.return_value = {"name": "domain", "label": "Domain Check", "passed": True, "message": "ok"}
    mock_mx.return_value = {"name": "mx", "label": "MX Record", "passed": True, "message": "ok"}
    mock_smtp.return_value = {"name": "smtp", "label": "SMTP Verification", "passed": True, "message": "ok"}

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
    mock_domain.return_value = {"name": "domain", "label": "Domain Check", "passed": True, "message": "ok"}
    mock_mx.return_value = {"name": "mx", "label": "MX Record", "passed": True, "message": "ok"}
    mock_smtp.return_value = {"name": "smtp", "label": "SMTP Verification", "passed": True, "message": "ok"}

    emails = ["user1@gmail.com", "user2@gmail.com", "bad-email"]
    results = asyncio.get_event_loop().run_until_complete(validate_bulk_async(emails))

    assert len(results) == 3
    assert results[0]["verdict"] == "valid"
    assert results[1]["verdict"] == "valid"
    assert results[2]["verdict"] == "invalid"
