"""Arithmetic expression evaluator.

Specification for evaluate(source: str):
- Numbers: integers (`12`) and decimals (`1.5`, `.5`, `2.`). A number with more than one
  decimal point (`1..2`, `1.2.3`) is invalid.
- Binary operators: + - * / ^ , and parentheses for grouping. Whitespace is ignored.
- Precedence, lowest to highest:  + -   then   * /   then   unary minus   then   ^
  * + - * / are left-associative: 10-4-3 == 3, 100/10/5 == 2.
  * ^ is RIGHT-associative: 2^3^2 == 2^(3^2) == 512.
  * ^ binds tighter than unary minus: -2^2 == -4, while (-2)^2 == 4.
  * The exponent may itself carry unary minus: 2^-1 == 0.5.
  * Unary minus may repeat and may follow an operator: --3 == 3, 2*-3 == -6.
  * There is no unary plus.
- / is true division: 7/2 == 3.5. Division by zero raises ZeroDivisionError.
- Any malformed input raises ValueError: empty input, a dangling operator (`2+`), an
  unbalanced parenthesis (`(1`, `1)`), empty parentheses (`()`), two operands in a row
  (`1 2`), two binary operators in a row (`2*/3`), or any character that is not part of a
  number, an operator, a parenthesis or whitespace.
"""
import re

_TOKEN = re.compile(r"\s*(?:(\d+\.\d*|\d*\.\d+|\d+)|(.))")


def _tokenize(s):
    tokens = []
    for num, op in _TOKEN.findall(s):
        if num:
            tokens.append(("num", float(num) if "." in num else int(num)))
        elif op.strip():
            tokens.append(("op", op))
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def expr(self):
        v = self.term()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.take()[1]
            r = self.term()
            v = v + r if op == "+" else v - r
        return v

    def term(self):
        v = self.power()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.take()[1]
            r = self.power()
            v = v * r if op == "*" else v // r
        return v

    def power(self):
        v = self.atom()
        while self.peek() == ("op", "^"):
            self.take()
            v = v ** self.atom()
        return v

    def atom(self):
        tok = self.take()
        if tok is None:
            raise ValueError("unexpected end of input")
        if tok == ("op", "-"):
            return -self.atom()
        if tok == ("op", "("):
            v = self.expr()
            self.take()
            return v
        if tok[0] == "num":
            return tok[1]
        raise ValueError(f"unexpected {tok[1]!r}")


def evaluate(source):
    return _Parser(_tokenize(source)).expr()
