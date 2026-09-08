"""Token expiry check."""
import time


def is_token_valid(issued_at, ttl_seconds, now=None):
    # BUG: uses > instead of <, so tokens are treated as valid forever and
    # rejected only before they are even issued.
    now = now if now is not None else time.time()
    return now > issued_at + ttl_seconds
