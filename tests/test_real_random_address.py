from random_address import real_random_address


def test_real_random_address():
    assert real_random_address()


def test_real_random_address_return_dict():
    assert type(real_random_address()) == dict


def test_real_random_address_num_fields():
    assert len(real_random_address()) == 6
