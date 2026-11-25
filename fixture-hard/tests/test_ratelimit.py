import pytest

from pkg.ratelimit import TokenBucket


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_starts_full():
    b = TokenBucket(1, 3, clock=Clock())
    assert [b.allow() for _ in range(4)] == [True, True, True, False]


def test_fractional_refill_accumulates():
    c = Clock()
    b = TokenBucket(2, 1, clock=c)
    assert b.allow()
    c.t = 0.25
    assert not b.allow()
    c.t = 0.5
    assert b.allow()


def test_many_small_steps_accumulate():
    c = Clock()
    b = TokenBucket(1, 1, clock=c)
    assert b.allow()
    for i in range(1, 8):
        c.t = i * 0.125
        assert not b.allow()
    c.t = 1.0
    assert b.allow()


def test_capped_at_capacity():
    c = Clock()
    b = TokenBucket(10, 2, clock=c)
    c.t = 100.0
    assert b.tokens == pytest.approx(2.0)
    assert [b.allow() for _ in range(3)] == [True, True, False]


def test_failure_consumes_nothing():
    c = Clock()
    b = TokenBucket(1, 2, clock=c)
    assert b.allow(2)
    assert not b.allow()
    assert not b.allow()
    c.t = 1.0
    assert b.allow()


def test_cost():
    b = TokenBucket(1, 5, clock=Clock())
    assert b.allow(3)
    assert not b.allow(3)
    assert b.allow(2)


def test_cost_over_capacity():
    b = TokenBucket(1, 2, clock=Clock())
    with pytest.raises(ValueError):
        b.allow(3)


@pytest.mark.parametrize("rate,cap", [(0, 1), (1, 0), (-1, 1), (1, -2)])
def test_bad_params(rate, cap):
    with pytest.raises(ValueError):
        TokenBucket(rate, cap, clock=Clock())


def test_tokens_property():
    c = Clock()
    b = TokenBucket(4, 8, clock=c)
    assert b.allow(8)
    c.t = 0.5
    assert b.tokens == pytest.approx(2.0)


def test_default_clock():
    assert TokenBucket(1, 1).allow()
