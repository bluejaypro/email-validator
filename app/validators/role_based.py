from app.config import DATA_DIR

_role_prefixes: frozenset | None = None


def _load_prefixes() -> frozenset:
    global _role_prefixes
    if _role_prefixes is None:
        path = DATA_DIR / "role_prefixes.txt"
        with open(path) as f:
            _role_prefixes = frozenset(
                line.strip().lower() for line in f if line.strip()
            )
    return _role_prefixes


def check_role_based(email: str) -> dict:
    """Check if the email is a role-based address (e.g., admin@, info@)."""
    local = email.rsplit("@", 1)[0].lower()
    prefixes = _load_prefixes()

    if local in prefixes:
        return {
            "name": "role_based",
            "label": "Role-Based Address",
            "passed": False,
            "message": f"'{local}@' is a role-based address",
        }

    return {
        "name": "role_based",
        "label": "Role-Based Address",
        "passed": True,
        "message": "Not a role-based address",
    }
