def _tokenize(s):
    tokens, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit() or c == ".":
            j = i
            while j < len(s) and (s[j].isdigit() or s[j] == "."):
                j += 1
            txt = s[i:j]
            if txt.count(".") > 1 or txt == ".":
                raise ValueError(f"bad number {txt!r}")
            tokens.append(("num", float(txt) if "." in txt else int(txt)))
            i = j
            continue
        if c in "+-*/^()":
            tokens.append(("op", c))
            i += 1
            continue
        raise ValueError(f"unexpected character {c!r}")
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.t, self.i = tokens, 0

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
        v = self.unary()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.take()[1]
            r = self.unary()
            v = v * r if op == "*" else v / r
        return v

    def unary(self):
        if self.peek() == ("op", "-"):
            self.take()
            return -self.unary()
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek() == ("op", "^"):
            self.take()
            return base ** self.unary()
        return base

    def atom(self):
        tok = self.take()
        if tok is None:
            raise ValueError("unexpected end of input")
        if tok[0] == "num":
            return tok[1]
        if tok == ("op", "("):
            v = self.expr()
            if self.take() != ("op", ")"):
                raise ValueError("missing )")
            return v
        raise ValueError(f"unexpected {tok[1]!r}")


def evaluate(source):
    p = _Parser(_tokenize(source))
    v = p.expr()
    if p.peek() is not None:
        raise ValueError("trailing input")
    return v
