from app.validators.disposable import check_disposable


def test_disposable_domain():
    result = check_disposable("test@mailinator.com")
    assert result["passed"] is False
    assert result["name"] == "disposable"


def test_disposable_guerrillamail():
    result = check_disposable("test@guerrillamail.com")
    assert result["passed"] is False


def test_non_disposable():
    result = check_disposable("test@gmail.com")
    assert result["passed"] is True


def test_non_disposable_corporate():
    result = check_disposable("user@company.org")
    assert result["passed"] is True
