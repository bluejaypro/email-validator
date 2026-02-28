from app.validators.syntax import check_syntax


def test_valid_email():
    result = check_syntax("user@example.com")
    assert result["passed"] is True
    assert result["name"] == "syntax"


def test_valid_email_with_plus():
    result = check_syntax("user+tag@example.com")
    assert result["passed"] is True


def test_valid_email_with_dots():
    result = check_syntax("first.last@example.com")
    assert result["passed"] is True


def test_empty_email():
    result = check_syntax("")
    assert result["passed"] is False
    assert "empty" in result["message"].lower()


def test_missing_at():
    result = check_syntax("userexample.com")
    assert result["passed"] is False


def test_no_local_part():
    result = check_syntax("@example.com")
    assert result["passed"] is False


def test_no_domain():
    result = check_syntax("user@")
    assert result["passed"] is False


def test_consecutive_dots():
    result = check_syntax("user..name@example.com")
    assert result["passed"] is False


def test_leading_dot():
    result = check_syntax(".user@example.com")
    assert result["passed"] is False


def test_trailing_dot():
    result = check_syntax("user.@example.com")
    assert result["passed"] is False


def test_too_long_email():
    local = "a" * 65
    result = check_syntax(f"{local}@example.com")
    assert result["passed"] is False


def test_invalid_characters():
    result = check_syntax("user name@example.com")
    assert result["passed"] is False


def test_single_char_tld():
    result = check_syntax("user@example.c")
    assert result["passed"] is False
