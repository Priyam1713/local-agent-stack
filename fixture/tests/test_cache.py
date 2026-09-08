from pkg.cache import expensive_square, reset_call_count, get_call_count

def test_memoizes_repeated_calls():
    reset_call_count()
    assert expensive_square(4) == 16
    assert expensive_square(4) == 16
    assert expensive_square(4) == 16
    assert get_call_count() == 1

def test_different_args_both_compute():
    reset_call_count()
    assert expensive_square(2) == 4
    assert expensive_square(3) == 9
    assert get_call_count() == 2
