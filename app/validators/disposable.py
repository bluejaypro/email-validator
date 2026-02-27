from app.config import DATA_DIR

_disposable_domains: frozenset | None = None


def _load_domains() -> frozenset:
    global _disposable_domains
    if _disposable_domains is None:
        path = DATA_DIR / "disposable_domains.txt"
        with open(path) as f:
            _disposable_domains = frozenset(
                line.strip().lower() for line in f if line.strip()
            )
    return _disposable_domains


def check_disposable(email: str) -> dict:
    """Check if the email uses a disposable/temporary email provider."""
    domain = email.rsplit("@", 1)[1].lower()
    domains = _load_domains()

    if domain in domains:
        return {
            "name": "disposable",
            "label": "Disposable Email",
            "passed": False,
            "message": f"'{domain}' is a disposable email provider",
        }

    return {
        "name": "disposable",
        "label": "Disposable Email",
        "passed": True,
        "message": "Not a disposable email",
    }
