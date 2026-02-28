from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

_mock_result = {
    "email": "test@example.com",
    "is_valid": True,
    "score": 1.0,
    "verdict": "valid",
    "suggestion": None,
    "checks": [
        {"name": "syntax", "label": "Syntax", "passed": True, "message": "ok"}
    ],
}


# --- HTML & Static ---

def test_root_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_static_css():
    response = client.get("/static/css/style.css")
    assert response.status_code == 200


def test_static_js():
    response = client.get("/static/js/app.js")
    assert response.status_code == 200


# --- Health check ---

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- Security headers ---

def test_security_headers():
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "Referrer-Policy" in response.headers


# --- Single validation ---

@patch("app.api.routes.validate_email_async", new_callable=AsyncMock)
def test_validate_single(mock_validate):
    mock_validate.return_value = _mock_result
    response = client.post("/api/validate", json={"email": "test@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["verdict"] == "valid"


def test_validate_empty_email():
    response = client.post("/api/validate", json={"email": ""})
    assert response.status_code == 422


def test_validate_missing_body():
    response = client.post("/api/validate", json={})
    assert response.status_code == 422


# --- Bulk validation ---

@patch("app.api.routes.validate_bulk_async", new_callable=AsyncMock)
def test_validate_bulk(mock_bulk):
    mock_bulk.return_value = [_mock_result, _mock_result]
    response = client.post(
        "/api/validate/bulk",
        json={"emails": ["test@example.com", "other@example.com"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["valid"] == 2


def test_validate_bulk_empty_list():
    response = client.post("/api/validate/bulk", json={"emails": []})
    assert response.status_code == 422


# --- File upload ---

@patch("app.api.routes.validate_bulk_async", new_callable=AsyncMock)
def test_validate_bulk_upload_txt(mock_bulk):
    mock_bulk.return_value = [_mock_result]
    content = b"test@example.com\nother@example.com\n"
    response = client.post(
        "/api/validate/bulk/upload",
        files={"file": ("emails.txt", content, "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1


@patch("app.api.routes.validate_bulk_async", new_callable=AsyncMock)
def test_validate_bulk_upload_csv(mock_bulk):
    mock_bulk.return_value = [_mock_result]
    content = b"email\ntest@example.com\n"
    response = client.post(
        "/api/validate/bulk/upload",
        files={"file": ("emails.csv", content, "text/csv")},
    )
    assert response.status_code == 200


def test_upload_invalid_extension():
    content = b"test@example.com"
    response = client.post(
        "/api/validate/bulk/upload",
        files={"file": ("emails.json", content, "application/json")},
    )
    assert response.status_code == 400
    assert "Only .csv and .txt" in response.json()["detail"]


def test_upload_no_emails_found():
    content = b"no emails here\njust text\n"
    response = client.post(
        "/api/validate/bulk/upload",
        files={"file": ("data.txt", content, "text/plain")},
    )
    assert response.status_code == 400
    assert "No email addresses found" in response.json()["detail"]


def test_upload_non_utf8():
    content = b"\xff\xfe invalid utf8"
    response = client.post(
        "/api/validate/bulk/upload",
        files={"file": ("emails.txt", content, "text/plain")},
    )
    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]


# --- Error handling ---

@patch("app.api.routes.validate_email_async", new_callable=AsyncMock)
def test_validate_single_internal_error(mock_validate):
    mock_validate.side_effect = RuntimeError("boom")
    response = client.post("/api/validate", json={"email": "test@example.com"})
    assert response.status_code == 500
    assert "unexpectedly" in response.json()["detail"]


@patch("app.api.routes.validate_bulk_async", new_callable=AsyncMock)
def test_validate_bulk_internal_error(mock_bulk):
    mock_bulk.side_effect = RuntimeError("boom")
    response = client.post(
        "/api/validate/bulk",
        json={"emails": ["test@example.com"]},
    )
    assert response.status_code == 500
