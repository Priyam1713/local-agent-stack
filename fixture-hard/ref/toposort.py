import heapq


class CycleError(ValueError):
    def __init__(self, cycle):
        super().__init__("dependency cycle: " + " -> ".join(cycle))
        self.cycle = cycle


def order(deps):
    nodes = set(deps)
    for ds in deps.values():
        nodes.update(ds)
    remaining = {n: set(deps.get(n, ())) for n in nodes}
    dependents = {n: set() for n in nodes}
    for n, ds in remaining.items():
        for d in ds:
            dependents[d].add(n)
    ready = [n for n in nodes if not remaining[n]]
    heapq.heapify(ready)
    out = []
    while ready:
        n = heapq.heappop(ready)
        out.append(n)
        for m in dependents[n]:
            remaining[m].discard(n)
            if not remaining[m]:
                heapq.heappush(ready, m)
    if len(out) < len(nodes):
        left = {n for n in nodes if remaining[n]}
        path, pos, n = [], {}, min(left)
        while n not in pos:
            pos[n] = len(path)
            path.append(n)
            n = min(d for d in remaining[n] if d in left)
        raise CycleError(path[pos[n]:] + [n])
    return out
