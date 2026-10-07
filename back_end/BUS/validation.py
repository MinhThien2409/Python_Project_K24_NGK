"""Shared server-side input validators."""
import re

NATIONAL_ID_REGEX = re.compile(r"^(?:\d{9}|\d{12})$")


def validate_national_id(value, required=False):
    """Validate Vietnamese CMND/CCCD as exactly 9 or 12 digits."""
    if value is None or not str(value).strip():
        if required:
            return False, "CMND/CCCD không được để trống!"
        return True, None
    value = str(value).strip()
    if not NATIONAL_ID_REGEX.fullmatch(value):
        return False, "CMND/CCCD phải gồm đúng 9 hoặc 12 chữ số!"
    return True, None
