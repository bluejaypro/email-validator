from app.validators.syntax import check_syntax
from app.validators.disposable import check_disposable
from app.validators.role_based import check_role_based
from app.validators.domain import check_domain
from app.validators.mx import check_mx
from app.validators.smtp import check_smtp


def validate_email(email: str) -> dict:
    """Run the full validation pipeline on a single email address."""
    email = email.strip()
    checks = []
    suggestion = None

    # Step 1: Syntax
    syntax_result = check_syntax(email)
    checks.append(syntax_result)
    if not syntax_result["passed"]:
        return _build_result(email, checks, score=0.0, verdict="invalid")

    # Step 2: Disposable
    disp_result = check_disposable(email)
    checks.append(disp_result)

    # Step 3: Role-based
    role_result = check_role_based(email)
    checks.append(role_result)

    # Step 4: Domain (+ typo detection)
    domain_result = check_domain(email)
    checks.append(domain_result)
    if "suggestion" in domain_result:
        suggestion = domain_result["suggestion"]
    if not domain_result["passed"]:
        score = 0.3 if suggestion else 0.1
        verdict = "warning" if suggestion else "invalid"
        return _build_result(email, checks, score=score, verdict=verdict, suggestion=suggestion)

    # Step 5: MX Record
    mx_result = check_mx(email)
    checks.append(mx_result)
    if not mx_result["passed"]:
        return _build_result(email, checks, score=0.1, verdict="invalid")

    # Step 6: SMTP Verification
    smtp_result = check_smtp(email)
    checks.append(smtp_result)

    # Compute final score and verdict
    score, verdict = _compute_score(checks, disp_result, role_result, smtp_result)
    return _build_result(email, checks, score=score, verdict=verdict, suggestion=suggestion)


def _compute_score(checks, disp_result, role_result, smtp_result):
    if not disp_result["passed"]:
        return 0.4, "warning"
    if not role_result["passed"]:
        if smtp_result["passed"]:
            return 0.7, "warning"
        return 0.5, "warning"
    if smtp_result["passed"] is None:
        return 0.6, "unknown"
    if smtp_result["passed"]:
        return 1.0, "valid"
    return 0.2, "invalid"


def _build_result(email, checks, score, verdict, suggestion=None):
    return {
        "email": email,
        "is_valid": verdict == "valid",
        "score": round(score, 2),
        "verdict": verdict,
        "suggestion": suggestion,
        "checks": checks,
    }
