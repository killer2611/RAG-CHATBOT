from __future__ import annotations

import re

_SESSION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def validate_session_id(value: str) -> str:
    value = value.strip()
    if not _SESSION_ID.fullmatch(value):
        raise ValueError("Invalid session_id format")
    return value
