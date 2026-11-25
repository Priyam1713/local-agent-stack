"""Shell-style variable expansion.

Specification for expand(template: str, env: dict[str, str]) -> str:
- A NAME is [A-Za-z_][A-Za-z0-9_]* , matched greedily ("$USER_x" refers to USER_x).
- $NAME and ${NAME} are replaced by env[NAME]; if NAME is not in env, raise KeyError(NAME).
- ${NAME:-default}  uses `default` if NAME is unset OR set to the empty string.
- ${NAME-default}   uses `default` only if NAME is unset.
- `default` is itself a template and may contain $NAME, ${...} and nested defaults such as
  ${A:-${B:-x}}. It is expanded ONLY if it is actually used, so an unused default that
  refers to a missing variable is not an error.
- $$ produces a single literal $.
- A $ that is not followed by a NAME start, "{" or "$" is a literal $ ("cost $5", "end $").
- Inserted values are never re-scanned: if env["A"] == "$B", "$A" expands to "$B".
- ValueError for an unterminated "${", an empty or invalid name inside braces ("${}",
  "${1X}"), and any other operator after the name ("${A:?x}", "${A+x}").
"""
import re


def expand(template, env):
    return re.sub(r"\$(\w+)", lambda m: env[m.group(1)], template)
