from pathlib import Path

from app.core.security import validate_session_id


def test_session_id_validation():
    assert validate_session_id("user_123") == "user_123"
    try:
        validate_session_id("../../etc/passwd")
    except ValueError:
        pass
    else:
        raise AssertionError("path traversal session id should be rejected")
