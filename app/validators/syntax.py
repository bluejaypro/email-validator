import re

# RFC 5322 compliant pattern (practical subset)
# Allows: letters, digits, ._%+- in local part; letters, digits, .- in domain; 2-63 char TLD
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,63}$"
)

# Additional checks beyond basic regex
MAX_LOCAL_LENGTH = 64
MAX_DOMAIN_LENGTH = 253
MAX_TOTAL_LENGTH = 254


def check_syntax(email: str) -> dict:
    """Validate email syntax against RFC 5322 rules."""
    email = email.strip()

    if not email:
        return _fail("Email address is empty")

    if len(email) > MAX_TOTAL_LENGTH:
        return _fail(f"Email exceeds {MAX_TOTAL_LENGTH} characters")

    if "@" not in email:
        return _fail("Missing '@' symbol")

    parts = email.rsplit("@", 1)
    local, domain = parts[0], parts[1]

    if not local:
        return _fail("Local part (before @) is empty")

    if len(local) > MAX_LOCAL_LENGTH:
        return _fail(f"Local part exceeds {MAX_LOCAL_LENGTH} characters")

    if not domain:
        return _fail("Domain (after @) is empty")

    if len(domain) > MAX_DOMAIN_LENGTH:
        return _fail(f"Domain exceeds {MAX_DOMAIN_LENGTH} characters")

    if local.startswith(".") or local.endswith("."):
        return _fail("Local part cannot start or end with a dot")

    if ".." in local:
        return _fail("Local part cannot contain consecutive dots")

    if not EMAIL_REGEX.match(email):
        return _fail("Contains invalid characters")

    return {
        "name": "syntax",
        "label": "Syntax (RFC 5322)",
        "passed": True,
        "message": "Valid syntax",
    }


def _fail(reason: str) -> dict:
    return {
        "name": "syntax",
        "label": "Syntax (RFC 5322)",
        "passed": False,
        "message": reason,
    }
