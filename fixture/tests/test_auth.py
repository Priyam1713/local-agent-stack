from pkg.auth import is_token_valid

def test_fresh_token_is_valid():
    assert is_token_valid(issued_at=100, ttl_seconds=60, now=110) is True

def test_expired_token_is_invalid():
    assert is_token_valid(issued_at=100, ttl_seconds=60, now=200) is False
