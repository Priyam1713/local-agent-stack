import pytest

from pkg.calc import evaluate


@pytest.mark.parametrize(
    "src,want",
    [
        ("1+2*3", 7),
        ("(1+2)*3", 9),
        ("7/2", 3.5),
        ("8/4", 2),
        ("2^3^2", 512),
        ("-2^2", -4),
        ("(-2)^2", 4),
        ("2^-1", 0.5),
        ("2*-3", -6),
        ("--3", 3),
        ("10-4-3", 3),
        ("100/10/5", 2),
        (" 1.5 + .5 ", 2.0),
        ("2.*2", 4.0),
        ("2^2*3", 12),
        ("-(1+2)*2", -6),
        ("3-(-2)", 5),
        ("((4))", 4),
    ],
)
def test_values(src, want):
    assert evaluate(src) == pytest.approx(want)


def test_true_division():
    assert evaluate("7/2") == 3.5
    assert evaluate("1/4") == 0.25


@pytest.mark.parametrize("src", ["", "   ", "2+", "(1", "1)", "()", "1 2", "2*/3", "abc", "1..2", "1.2.3", "+3"])
def test_invalid(src):
    with pytest.raises(ValueError):
        evaluate(src)


def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        evaluate("1/0")
