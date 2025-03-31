"""
Tests for random_address module
"""
from random_address import real_random_address
from random_address import real_random_address_by_state
from random_address import real_random_address_by_postal_code


def test_real_random_address():
    """Test default return as TRUE"""
    assert real_random_address()


def test_real_random_address_return_dict():
    """Test type of return as dict"""
    assert isinstance(real_random_address(), dict)


def test_real_random_address_num_fields():
    """Test number of elements of dict returned"""
    assert len(real_random_address()) == 6


def test_real_random_address_fields():
    """Test that the random address has all expected fields"""
    address = real_random_address()
    expected_fields = {'address1', 'address2', 'city', 'state', 'postalCode', 'coordinates'}
    assert expected_fields == set(address.keys())


def test_real_random_address_by_state():
    """Test return with a valid state code and validate content"""
    for state in ['CA', 'FL', 'AK']:
        address = real_random_address_by_state(state)
        assert isinstance(address, dict)
        assert address.get('state') == state


def test_real_random_address_by_state_with_no_results():
    """Test return with a state code with no results"""
    assert not real_random_address_by_state('NY')


def test_real_random_address_by_postal_code():
    """Test return with a valid postal code and validate content"""
    postal_codes = ['99577', '32409', '94560']
    for code in postal_codes:
        address = real_random_address_by_postal_code(code)
        assert isinstance(address, dict)
        assert address.get('postalCode') == code


def test_real_random_address_by_postal_code_with_no_results():
    """Test return with a postal code with no results"""
    assert not real_random_address_by_postal_code('90210')
