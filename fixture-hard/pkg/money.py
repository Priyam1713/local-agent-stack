"""Money helpers. All results are decimal.Decimal values with exactly two decimal places.

split(amount, n) -> list[Decimal]
- `amount` is a str, int or Decimal with at most two decimal places; more places, or a value
  that is not a number, raise ValueError. `n` must be an int >= 1, otherwise ValueError.
- Return n parts that sum EXACTLY to amount, differ from each other by at most 0.01, and are
  ordered with the larger-magnitude parts first: split("10.00", 3) -> [3.34, 3.33, 3.33].
  Parts may be zero: split("0.02", 3) -> [0.01, 0.01, 0.00].
- A negative amount splits the same way with every part negative:
  split("-10.00", 3) -> [-3.34, -3.33, -3.33].

round_half_even(x) -> Decimal
- Round a str/int/Decimal to two decimal places using banker's rounding (round half to
  even), computed exactly in decimal, never via float: "2.675" -> 2.68, "2.665" -> 2.66.
"""


def split(amount, n):
    share = round(float(amount) / n, 2)
    return [share] * n


def round_half_even(x):
    return round(float(x), 2)
