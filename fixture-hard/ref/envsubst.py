import re

_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _match_brace(s, open_idx):
    depth = 0
    for k in range(open_idx, len(s)):
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                return k
    raise ValueError("unterminated ${")


def _brace(inner, env):
    m = _NAME.match(inner)
    if not m:
        raise ValueError(f"invalid name in ${{{inner}}}")
    name, rest = m.group(0), inner[m.end():]
    if rest == "":
        if name not in env:
            raise KeyError(name)
        return env[name]
    if rest.startswith(":-"):
        val = env.get(name)
        return val if val else expand(rest[2:], env)
    if rest.startswith("-"):
        return env[name] if name in env else expand(rest[1:], env)
    raise ValueError(f"unsupported operator in ${{{inner}}}")


def expand(template, env):
    out, i, n = [], 0, len(template)
    while i < n:
        c = template[i]
        if c != "$" or i + 1 >= n:
            out.append(c)
            i += 1
            continue
        nxt = template[i + 1]
        if nxt == "$":
            out.append("$")
            i += 2
            continue
        if nxt == "{":
            j = _match_brace(template, i + 1)
            out.append(_brace(template[i + 2:j], env))
            i = j + 1
            continue
        m = _NAME.match(template, i + 1)
        if m:
            if m.group(0) not in env:
                raise KeyError(m.group(0))
            out.append(env[m.group(0)])
            i = m.end()
            continue
        out.append("$")
        i += 1
    return "".join(out)
