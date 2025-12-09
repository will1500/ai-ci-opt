import pytest
from sample_app.app import add

def test_add():
    assert add(1, 2) == 3

def test_add_negative():
    assert add(-1, -1) == -2

def test_flaky_example():
    import random
    if random.random() < 0.3:
        pytest.skip("simulating flakiness")
    assert add(2, 2) == 4
