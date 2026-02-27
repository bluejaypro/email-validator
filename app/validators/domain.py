import json
import socket

from app.config import DATA_DIR, DNS_TIMEOUT

_typo_map: dict | None = None


def _load_typo_map() -> dict:
    global _typo_map
    if _typo_map is None:
        path = DATA_DIR / "domain_typos.json"
        with open(path) as f:
            _typo_map = json.load(f)
    return _typo_map


def check_domain(email: str) -> dict:
    """Verify the domain exists and check for common typos."""
    domain = email.rsplit("@", 1)[1].lower()
    local = email.rsplit("@", 1)[0]
    typo_map = _load_typo_map()

    # Check for known typos first
    suggestion = None
    if domain in typo_map:
        correct = typo_map[domain]
        suggestion = f"{local}@{correct}"
        return {
            "name": "domain",
            "label": "Domain Check",
            "passed": False,
            "message": f"Possible typo. Did you mean '{correct}'?",
            "suggestion": suggestion,
        }

    # Verify domain resolves
    try:
        socket.setdefaulttimeout(DNS_TIMEOUT)
        socket.getaddrinfo(domain, None)
        return {
            "name": "domain",
            "label": "Domain Check",
            "passed": True,
            "message": "Domain exists",
        }
    except socket.gaierror:
        return {
            "name": "domain",
            "label": "Domain Check",
            "passed": False,
            "message": f"Domain '{domain}' does not exist",
        }
