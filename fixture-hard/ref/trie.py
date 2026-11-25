class _Node:
    def __init__(self):
        self.children = {}
        self.weight = None


class Trie:
    def __init__(self):
        self._root = _Node()
        self._count = 0

    def insert(self, word, weight=1):
        if not word or weight <= 0:
            raise ValueError("word must be non-empty and weight > 0")
        node = self._root
        for ch in word.lower():
            node = node.children.setdefault(ch, _Node())
        if node.weight is None:
            node.weight = weight
            self._count += 1
        else:
            node.weight += weight

    def _find(self, prefix):
        node = self._root
        for ch in prefix.lower():
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def __contains__(self, word):
        node = self._find(word)
        return node is not None and node.weight is not None

    def __len__(self):
        return self._count

    def top_k(self, prefix, k):
        if k <= 0:
            return []
        node = self._find(prefix)
        if node is None:
            return []
        found, stack = [], [(node, prefix.lower())]
        while stack:
            n, w = stack.pop()
            if n.weight is not None:
                found.append((w, n.weight))
            for ch, child in n.children.items():
                stack.append((child, w + ch))
        found.sort(key=lambda t: (-t[1], t[0]))
        return [w for w, _ in found[:k]]

    def delete(self, word):
        path, node = [], self._root
        for ch in word.lower():
            if ch not in node.children:
                return False
            path.append((node, ch))
            node = node.children[ch]
        if node.weight is None:
            return False
        node.weight = None
        self._count -= 1
        for parent, ch in reversed(path):
            child = parent.children[ch]
            if child.weight is None and not child.children:
                del parent.children[ch]
            else:
                break
        return True

    def node_count(self):
        count, stack = 0, [self._root]
        while stack:
            n = stack.pop()
            count += 1
            stack.extend(n.children.values())
        return count
