from decimal import Decimal as D

import pytest

from pkg.money import round_half_even, split


def test_even_split():
    assert split("10.00", 4) == [D("2.50")] * 4


def test_remainder_goes_first():
    assert split("10.00", 3) == [D("3.34"), D("3.33"), D("3.33")]


def test_invariants_over_many_inputs():
    for amt in ["0.01", "0.05", "1.00", "100.00", "999.99", "1234.56"]:
        for n in range(1, 13):
            parts = split(amt, n)
            assert len(parts) == n
            assert sum(parts) == D(amt)
            assert max(parts) - min(parts) <= D("0.01")
            assert parts == sorted(parts, reverse=True)


def test_more_parts_than_cents():
    assert split("0.02", 3) == [D("0.01"), D("0.01"), D("0.00")]


def test_negative():
    assert split("-10.00", 3) == [D("-3.34"), D("-3.33"), D("-3.33")]


def test_int_and_decimal_input():
    assert split(5, 2) == [D("2.50"), D("2.50")]
    assert split(D("1.00"), 3) == [D("0.34"), D("0.33"), D("0.33")]


def test_results_are_two_place_decimals():
    for p in split("1.00", 3) + split(7, 2):
        assert isinstance(p, D)
        assert p.as_tuple().exponent == -2


def test_too_many_places():
    with pytest.raises(ValueError):
        split("1.005", 2)


@pytest.mark.parametrize("n", [0, -1])
def test_bad_n(n):
    with pytest.raises(ValueError):
        split("1.00", n)


def test_not_a_number():
    with pytest.raises(ValueError):
        split("abc", 2)


@pytest.mark.parametrize(
    "x,want",
    [("2.675", "2.68"), ("2.665", "2.66"), ("2.645", "2.64"), ("0.125", "0.12"),
     ("0.135", "0.14"), ("-1.005", "-1.00"), ("1.0051", "1.01"), ("3", "3.00")],
)
def test_round_half_even(x, want):
    got = round_half_even(x)
    assert isinstance(got, D)
    assert got == D(want)
    assert got.as_tuple().exponent == -2
