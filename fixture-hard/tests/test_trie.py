import pytest

from pkg.trie import Trie


def make():
    t = Trie()
    for w, wt in [("car", 5), ("cart", 3), ("carbon", 5), ("care", 1), ("dog", 2), ("Card", 4)]:
        t.insert(w, wt)
    return t


def test_top_k_order():
    assert make().top_k("car", 3) == ["car", "carbon", "card"]


def test_top_k_all():
    assert make().top_k("car", 10) == ["car", "carbon", "card", "cart", "care"]


def test_case_insensitive():
    t = make()
    assert t.top_k("CA", 1) == ["car"]
    assert "CARD" in t and "card" in t


def test_weights_accumulate():
    t = make()
    t.insert("care", 10)
    assert t.top_k("car", 1) == ["care"]
    assert len(t) == 6


def test_empty_prefix_matches_all():
    assert make().top_k("", 2) == ["car", "carbon"]


def test_k_zero_and_missing_prefix():
    t = make()
    assert t.top_k("car", 0) == []
    assert t.top_k("zebra", 5) == []


def test_len_and_contains():
    t = make()
    assert len(t) == 6
    assert "ca" not in t and "dog" in t


def test_delete_prunes():
    t = Trie()
    t.insert("abc")
    t.insert("abd")
    assert t.node_count() == 5
    assert t.delete("abd") is True
    assert t.node_count() == 4
    assert "abd" not in t and len(t) == 1
    assert t.delete("abd") is False
    assert t.delete("ab") is False
    assert t.delete("ABC") is True
    assert t.node_count() == 1 and len(t) == 0


def test_delete_keeps_shorter_word():
    t = Trie()
    t.insert("car")
    t.insert("cart")
    assert t.delete("cart")
    assert "car" in t and t.node_count() == 4


def test_delete_keeps_longer_word():
    t = Trie()
    t.insert("car")
    t.insert("cart")
    assert t.delete("car")
    assert "cart" in t and "car" not in t
    assert t.top_k("ca", 5) == ["cart"]
    assert t.node_count() == 5


def test_invalid_insert():
    t = Trie()
    with pytest.raises(ValueError):
        t.insert("", 1)
    with pytest.raises(ValueError):
        t.insert("x", 0)
