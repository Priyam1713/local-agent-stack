"""Two validators with near-duplicated logic.

TASK: validate_username and validate_email both independently implement the
same "3-32 chars, no whitespace" check, copy-pasted rather than shared.
Extract that shared rule into one helper (e.g. `_check_length_and_no_space`)
and have both callers use it, without changing either function's public
behaviour (same inputs must still produce the same True/False results).
"""


def validate_username(name):
    if not (3 <= len(name) <= 32):
        return False
    if any(c.isspace() for c in name):
        return False
    return name.isascii()


def validate_email(email):
    if not (3 <= len(email) <= 32):
        return False
    if any(c.isspace() for c in email):
        return False
    return "@" in email and "." in email.split("@")[-1]
