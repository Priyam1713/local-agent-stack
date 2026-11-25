from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

CENT = Decimal("0.01")


def _dec(x):
    if isinstance(x, bool) or not isinstance(x, (str, int, Decimal)):
        raise ValueError(f"unsupported amount {x!r}")
    try:
        d = x if isinstance(x, Decimal) else Decimal(str(x).strip())
    except InvalidOperation:
        raise ValueError(f"not a number: {x!r}") from None
    if not d.is_finite():
        raise ValueError(f"not a finite number: {x!r}")
    return d


def split(amount, n):
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be an int >= 1")
    d = _dec(amount)
    if d != d.quantize(CENT):
        raise ValueError("more than two decimal places")
    sign = -1 if d < 0 else 1
    cents = int(abs(d) * 100)
    base, rem = divmod(cents, n)
    return [Decimal(base + (1 if i < rem else 0)) * CENT * sign for i in range(n)]


def round_half_even(x):
    return _dec(x).quantize(CENT, rounding=ROUND_HALF_EVEN)
