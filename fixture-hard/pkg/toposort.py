"""Dependency ordering.

`deps` maps each node to the nodes it depends on (a list or a set of strings). A node that
only ever appears as a dependency is still a node.

Specification for order(deps) -> list[str]:
- Return every node exactly once, with each node placed after all of its dependencies.
- Deterministic tie-breaking: whenever several nodes have all of their dependencies already
  placed, the lexicographically smallest of them goes next. (So the result is unique.)
- order({}) == [].
- `deps` must not be modified.
- If the dependencies contain a cycle, raise CycleError. CycleError is a subclass of
  ValueError and has a `.cycle` attribute: a list of nodes that follows dependency edges and
  starts and ends with the same node, so consecutive entries x, y always satisfy
  y in deps[x]. A node that depends on itself gives ['a', 'a'].
"""


class CycleError(ValueError):
    def __init__(self, cycle):
        super().__init__("dependency cycle: " + " -> ".join(cycle))
        self.cycle = cycle


def order(deps):
    out = []
    seen = set()

    def visit(n):
        if n in seen:
            return
        seen.add(n)
        for d in deps.get(n, ()):
            visit(d)
        out.append(n)

    for n in deps:
        visit(n)
    return out
