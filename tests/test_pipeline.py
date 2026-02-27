from unittest.mock import patch
from app.validators.pipeline import validate_email


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
