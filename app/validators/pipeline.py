import asyncio
import logging

from app.config import CONCURRENT_WORKERS
from app.validators.syntax import check_syntax
from app.validators.disposable import check_disposable
from app.validators.role_based import check_role_based
from app.validators.domain import check_domain, check_domain_async
from app.validators.mx import check_mx, check_mx_async
from app.validators.smtp import check_smtp, check_smtp_async

logger = logging.getLogger("email_validator.pipeline")


def validate_email(email: str) -> dict:
    """Run the full validation pipeline on a single email address (sync)."""
    email = email.strip()
    checks = []
    suggestion = None

    syntax_result = check_syntax(email)
    checks.append(syntax_result)
    if not syntax_result["passed"]:
        return _build_result(email, checks, score=0.0, verdict="invalid")

    disp_result = check_disposable(email)
    checks.append(disp_result)

    role_result = check_role_based(email)
    checks.append(role_result)

    domain_result = check_domain(email)
    checks.append(domain_result)
    if "suggestion" in domain_result:
        suggestion = domain_result["suggestion"]
    if not domain_result["passed"]:
        score = 0.3 if suggestion else 0.1
        verdict = "warning" if suggestion else "invalid"
        return _build_result(email, checks, score=score, verdict=verdict, suggestion=suggestion)

    mx_result = check_mx(email)
    checks.append(mx_result)
    if not mx_result["passed"]:
        return _build_result(email, checks, score=0.1, verdict="invalid")

    smtp_result = check_smtp(email)
    checks.append(smtp_result)

    score, verdict = _compute_score(disp_result, role_result, smtp_result)
    return _build_result(email, checks, score=score, verdict=verdict, suggestion=suggestion)


async def validate_email_async(email: str) -> dict:
    """Run the full validation pipeline on a single email address (async).

    Local checks (syntax, disposable, role-based) run synchronously since
    they are instant in-memory lookups. Network checks (domain, MX, SMTP)
    run in threads to avoid blocking the event loop.
    """
    email = email.strip()
    checks = []
    suggestion = None

    # Fast local checks (instant, no I/O)
    syntax_result = check_syntax(email)
    checks.append(syntax_result)
    if not syntax_result["passed"]:
        return _build_result(email, checks, score=0.0, verdict="invalid")

    disp_result = check_disposable(email)
    checks.append(disp_result)

    role_result = check_role_based(email)
    checks.append(role_result)

    # Network I/O checks (async)
    domain_result = await check_domain_async(email)
    checks.append(domain_result)
    if "suggestion" in domain_result:
        suggestion = domain_result["suggestion"]
    if not domain_result["passed"]:
        score = 0.3 if suggestion else 0.1
        verdict = "warning" if suggestion else "invalid"
        return _build_result(email, checks, score=score, verdict=verdict, suggestion=suggestion)

    mx_result = await check_mx_async(email)
    checks.append(mx_result)
    if not mx_result["passed"]:
        return _build_result(email, checks, score=0.1, verdict="invalid")

    smtp_result = await check_smtp_async(email)
    checks.append(smtp_result)

    score, verdict = _compute_score(disp_result, role_result, smtp_result)
    return _build_result(email, checks, score=score, verdict=verdict, suggestion=suggestion)


async def validate_bulk_async(emails: list[str]) -> list[dict]:
    """Validate a list of emails concurrently with rate limiting.

    Uses a semaphore to limit concurrent network operations to
    CONCURRENT_WORKERS to avoid overwhelming DNS/SMTP servers.
    """
    semaphore = asyncio.Semaphore(CONCURRENT_WORKERS)

    async def _limited(email: str) -> dict:
        async with semaphore:
            return await validate_email_async(email)

    logger.info("Starting bulk validation: %d emails, %d workers", len(emails), CONCURRENT_WORKERS)
    tasks = [_limited(email) for email in emails]
    results = await asyncio.gather(*tasks)
    logger.info("Bulk validation complete: %d emails processed", len(results))
    return list(results)


def _compute_score(
    disp_result: dict, role_result: dict, smtp_result: dict
) -> tuple[float, str]:
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


def _build_result(
    email: str,
    checks: list[dict],
    score: float,
    verdict: str,
    suggestion: str | None = None,
) -> dict:
    return {
        "email": email,
        "is_valid": verdict == "valid",
        "score": round(score, 2),
        "verdict": verdict,
        "suggestion": suggestion,
        "checks": checks,
    }
