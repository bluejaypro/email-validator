from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@patch("app.api.routes.validate_email")
def test_validate_single(mock_validate):
    mock_validate.return_value = {
        "email": "test@example.com",
        "is_valid": True,
        "score": 1.0,
        "verdict": "valid",
        "suggestion": None,
        "checks": [
            {"name": "syntax", "label": "Syntax", "passed": True, "message": "ok"}
        ],
    }

    response = client.post("/api/validate", json={"email": "test@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["verdict"] == "valid"


@patch("app.api.routes.validate_email")
def test_validate_bulk(mock_validate):
    mock_validate.return_value = {
        "email": "test@example.com",
        "is_valid": True,
        "score": 1.0,
        "verdict": "valid",
        "suggestion": None,
        "checks": [],
    }

    response = client.post(
        "/api/validate/bulk",
        json={"emails": ["test@example.com", "other@example.com"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_validate_empty_email():
    response = client.post("/api/validate", json={"email": ""})
    assert response.status_code == 422


def test_static_css():
    response = client.get("/static/css/style.css")
    assert response.status_code == 200


def test_static_js():
    response = client.get("/static/js/app.js")
    assert response.status_code == 200
