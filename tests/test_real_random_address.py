"""
Tests for random_address module
"""
from random_address import real_random_address


def test_real_random_address():
    """
    Test default return as TRUE
    """
    assert real_random_address()


def test_real_random_address_return_dict():
    """
    Test type of return as dict
    """
    assert isinstance(real_random_address(), dict)


def test_real_random_address_num_fields():
    """
    Test number of elements of dict returned
    """
    assert len(real_random_address()) == 6
