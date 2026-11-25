import pytest

from pkg.lru import LRUCache


def test_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert "a" not in c
    assert c.get("b") == 2 and c.get("c") == 3


def test_get_refreshes_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    c.put("c", 3)
    assert "b" not in c
    assert c.get("a") == 1


def test_update_refreshes_and_does_not_evict():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)
    assert len(c) == 2 and "b" in c
    c.put("c", 3)
    assert "b" not in c
    assert c.get("a") == 10


def test_contains_does_not_refresh():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert "a" in c
    c.put("c", 3)
    assert "a" not in c


def test_missing_key():
    assert LRUCache(1).get("nope") is None


def test_capacity_one():
    c = LRUCache(1)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") is None and c.get("b") == 2 and len(c) == 1


@pytest.mark.parametrize("cap", [0, -1])
def test_bad_capacity(cap):
    with pytest.raises(ValueError):
        LRUCache(cap)


def test_long_sequence():
    c = LRUCache(3)
    for i in range(10):
        c.put(i, i)
    c.get(7)
    c.put(10, 10)
    assert [k for k in range(11) if k in c] == [7, 9, 10]
