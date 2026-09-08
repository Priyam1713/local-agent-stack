from pkg.dedupe import validate_username, validate_email
import pkg.dedupe as dedupe_module
import inspect

def test_username_behaviour_unchanged():
    assert validate_username("bob") is True
    assert validate_username("ab") is False
    assert validate_username("this_name_is_way_too_long_to_be_valid_here") is False
    assert validate_username("has space") is False

def test_email_behaviour_unchanged():
    assert validate_email("a@b.co") is True
    assert validate_email("a@b") is False
    assert validate_email("no") is False
    assert validate_email("has space@b.co") is False

def test_shared_helper_actually_extracted():
    # Both functions must actually call a shared helper, not just happen to
    # both independently pass — otherwise this "fix" is cosmetic only.
    src = inspect.getsource(dedupe_module)
    assert src.count("len(") <= 1, (
        "expected the length check to be extracted into one shared helper, "
        "not duplicated inline in both functions"
    )
