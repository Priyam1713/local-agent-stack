from pkg.median import median

def test_odd_length():
    assert median([3, 1, 2]) == 2

def test_even_length_averages():
    assert median([1, 2, 3, 4]) == 2.5

def test_does_not_mutate_input():
    original = [3, 1, 2]
    median(original)
    assert original == [3, 1, 2]
