from app.validators.role_based import check_role_based


def test_admin_is_role_based():
    result = check_role_based("admin@company.com")
    assert result["passed"] is False
    assert result["name"] == "role_based"


def test_info_is_role_based():
    result = check_role_based("info@company.com")
    assert result["passed"] is False


def test_support_is_role_based():
    result = check_role_based("support@company.com")
    assert result["passed"] is False


def test_noreply_is_role_based():
    result = check_role_based("noreply@company.com")
    assert result["passed"] is False


def test_personal_not_role_based():
    result = check_role_based("john.doe@company.com")
    assert result["passed"] is True


def test_postmaster_is_role_based():
    result = check_role_based("postmaster@company.com")
    assert result["passed"] is False
