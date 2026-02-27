from pydantic import BaseModel, Field


class EmailRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=320, examples=["user@example.com"])


class BulkEmailRequest(BaseModel):
    emails: list[str] = Field(..., min_length=1, max_length=5000)


class CheckResult(BaseModel):
    name: str
    label: str
    passed: bool | None
    message: str


class ValidationResult(BaseModel):
    email: str
    is_valid: bool
    score: float
    verdict: str
    suggestion: str | None = None
    checks: list[CheckResult]


class BulkValidationResult(BaseModel):
    total: int
    valid: int
    invalid: int
    warnings: int
    unknown: int
    results: list[ValidationResult]
