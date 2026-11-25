import pytest

from pkg.intervals import insert, merge


def test_basic():
    assert merge([(1, 3), (2, 6), (8, 10), (15, 18)]) == [(1, 6), (8, 10), (15, 18)]


def test_touching_merge():
    assert merge([(1, 3), (3, 5)]) == [(1, 5)]


def test_unsorted():
    assert merge([(8, 10), (1, 3), (2, 6)]) == [(1, 6), (8, 10)]


def test_containment():
    assert merge([(1, 10), (2, 3), (4, 5)]) == [(1, 10)]


def test_points():
    assert merge([(2, 2), (2, 2), (1, 1)]) == [(1, 1), (2, 2)]


def test_empty():
    assert merge([]) == []


def test_input_not_mutated():
    data = [(5, 6), (1, 2)]
    merge(data)
    assert data == [(5, 6), (1, 2)]


def test_invalid():
    with pytest.raises(ValueError):
        merge([(1, 2), (3, 1)])


def test_insert_spanning():
    assert insert([(1, 2), (3, 5), (6, 7), (8, 10), (12, 16)], (4, 8)) == [(1, 2), (3, 10), (12, 16)]


def test_insert_at_ends():
    assert insert([(3, 5)], (1, 2)) == [(1, 2), (3, 5)]
    assert insert([(3, 5)], (6, 9)) == [(3, 5), (6, 9)]
    assert insert([(3, 5)], (5, 9)) == [(3, 9)]


def test_insert_empty():
    assert insert([], (1, 4)) == [(1, 4)]


def test_insert_not_mutated():
    data = [(1, 2)]
    insert(data, (3, 4))
    assert data == [(1, 2)]


def test_insert_invalid():
    with pytest.raises(ValueError):
        insert([(1, 2)], (5, 4))
