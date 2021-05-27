"""
Functions to retrieve a real random address that geocode successfully
"""
import json
import os
import random
import sys


def _get_address_dict_list():
    package_directory = os.path.dirname(sys.modules[__name__].__file__)
    source_filename_path = os.path.join(package_directory,
                                        'addresses-us-all.min.json')
    with open(source_filename_path, 'r') as source_filename:
        data = json.load(source_filename)
    return data


def real_random_address() -> dict:
    """
    Parameters
    ----------
    None

    Returns
    -------
    A dictionary with address information
    """
    package_directory = os.path.dirname(sys.modules[__name__].__file__)
    source_filename_path = os.path.join(package_directory,
                                        'addresses-us-all.min.json')
    with open(source_filename_path, 'r') as source_filename:
        data = json.load(source_filename)
    return random.choice(data.get('addresses'))


def real_random_address_by_state(state_code: str) -> dict:
    """
    Parameters
    ----------
    state_code (str):
        State code in two characters format to filter result by state
    (i.e CA, NY)

    Returns
    -------
    A dictionary with address information,
    if no address is found returns an empty dict.
    """
    data = _get_address_dict_list()
    filtered_data = []
    for element in data.get('addresses'):
        if element.get('state') == state_code:
            filtered_data.append(element)

    if len(filtered_data) > 0:
        return random.choice(filtered_data)
    return {}


def real_random_address_by_postal_code(postal_code: str) -> dict:
    """
    Parameters
    ----------
    postal_code (str):
        Postal code to filter result by state
    (i.e 32409, 94560)

    Returns
    -------
    A dictionary with address information,
    if no address is found returns an empty dict.
    """
    data = _get_address_dict_list()
    filtered_data = []
    for element in data.get('addresses'):
        if element.get('postalCode') == postal_code:
            filtered_data.append(element)

    if len(filtered_data) > 0:
        return random.choice(filtered_data)
    return {}
