"""
Tests for random_address module
"""
from random_address import real_random_address
from random_address import real_random_address_by_state
from random_address import real_random_address_by_postal_code


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


def test_real_random_address_by_state():
    """
    Test return with a code state
    """
    assert real_random_address_by_state('CA')
    assert real_random_address_by_state('FL')
    assert real_random_address_by_state('AK')


def test_real_random_address_by_state_with_no_results():
    """
        Test return with a code state with no results
        """
    assert not real_random_address_by_state('NY')


def test_real_random_address_by_postal_code():
    """
    Test return with a code state
    """
    assert real_random_address_by_postal_code('99577')
    assert real_random_address_by_postal_code('32409')
    assert real_random_address_by_postal_code('94560')


def test_real_random_address_by_postal_code_with_no_results():
    """
        Test return with a code state with no results
        """
    assert not real_random_address_by_postal_code('90210')
