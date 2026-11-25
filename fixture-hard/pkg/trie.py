"""Weighted autocomplete trie.

Specification:
- Words are case-insensitive: they are stored lowercased, and every lookup lowercases too.
- insert(word, weight=1): `word` must be non-empty and `weight` must be > 0, otherwise
  ValueError. Inserting a word that is already present ADDS weight to its existing weight.
- `word in trie` is True only for whole inserted words, not for mere prefixes.
- len(trie) is the number of distinct words.
- top_k(prefix, k): up to k words starting with `prefix`, ordered by weight descending,
  then alphabetically. k <= 0 gives []. An empty prefix matches every word.
- delete(word): remove the word and return True, or return False if it is not present
  (including when it is only a prefix of other words). Nodes that no longer lead to any word
  are pruned, so node_count() shrinks accordingly; nodes still needed by other words stay.
- node_count(): number of nodes including the root (an empty trie has 1).
"""


class _Node:
    def __init__(self):
        self.children = {}
        self.weight = None  # None means "no word ends here"


class Trie:
    def __init__(self):
        self._root = _Node()
        self._count = 0

    def insert(self, word, weight=1):
        node = self._root
        for ch in word:
            node = node.children.setdefault(ch, _Node())
        if node.weight is None:
            self._count += 1
        node.weight = weight

    def _find(self, prefix):
        node = self._root
        for ch in prefix:
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
        node = self._find(prefix)
        if node is None:
            return []
        found = []
        stack = [(node, prefix)]
        while stack:
            n, w = stack.pop()
            if n.weight is not None:
                found.append(w)
            for ch, child in n.children.items():
                stack.append((child, w + ch))
        return sorted(found)[:k]

    def delete(self, word):
        node = self._find(word)
        if node is None or node.weight is None:
            return False
        node.weight = None
        return True

    def node_count(self):
        count, stack = 0, [self._root]
        while stack:
            n = stack.pop()
            count += 1
            stack.extend(n.children.values())
        return count
