"""
Functions to retrieve a real random address that geocode successfully
"""

import json
import logging
import os
import random
import sys
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _get_address_dict_list() -> Dict[str, List[Dict[str, Any]]]:
    """Load the list of addresses from a local JSON file.

    Reads the 'addresses-us-all.min.json' file included in the package and
    returns the data as a dictionary.

    Returns:
        dict: Dictionary containing the addresses data with the structure:
            {'addresses': [address_dict, ...]}. If an error occurs, an empty list
            under the 'addresses' key is returned.
    """
    package_directory = os.path.dirname(sys.modules[__name__].__file__)
    source_filename_path = os.path.join(package_directory, "addresses-us-all.min.json")
    try:
        with open(source_filename_path, "r", encoding="utf-8") as source_file:
            data = json.load(source_file)
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Error loading addresses: %s", e)
        return {"addresses": []}


def real_random_address() -> Dict[str, Any]:
    """Retrieve a random real address from the dataset.

    Loads the dataset and returns a randomly selected address dictionary from
    the available entries.

    Returns:
        dict: Dictionary containing random address information, such as street,
        city, state, and postal code. Example:

        {
            'street': '123 Main St',
            'city': 'Los Angeles',
            'state': 'CA',
            'postalCode': '90001'
        }

        Returns an empty dictionary if no addresses are available.
    """
    data = _get_address_dict_list()
    return random.choice(data.get("addresses", []))


def real_random_address_by_state(state_code: str) -> Dict[str, Any]:
    """Retrieve a random real address filtered by US state code.

    Args:
        state_code (str): Two-letter state abbreviation (e.g., 'CA', 'NY').

    Returns:
        dict: Dictionary containing random address information matching the
        provided state.

    Example:
        >>> import random_address
        >>> random_address.real_random_address_by_state('CA')
        {
            'address1': '37600 Sycamore Street',
            'address2': '',
            'city': 'Newark',
            'state': 'CA',
            'postalCode': '94560',
            'coordinates': {'lat': 37.5261943, 'lng': -122.0304698}
        }

        Returns an empty dictionary if no addresses match the specified state.
    """
    data = _get_address_dict_list()
    filtered_data = [
        addr for addr in data.get("addresses", []) if addr.get("state") == state_code
    ]
    return random.choice(filtered_data) if filtered_data else {}


def real_random_address_by_postal_code(postal_code: str) -> Dict[str, Any]:
    """Retrieve a random real address filtered by US postal code.

    Args:
        postal_code (str): Postal code to filter the addresses by (e.g., '32409').

    Returns:
        dict: Dictionary containing random address information matching the
        provided postal code.

    Example:
        >>> import random_address
        >>> random_address.real_random_address_by_postal_code('32409')
        {
            'address1': '711 Tashanna Lane',
            'address2': '',
            'city': 'Southport',
            'state': 'FL',
            'postalCode': '32409',
            'coordinates': {'lat': 30.41437699999999, 'lng': -85.676568}
        }

        Returns an empty dictionary if no addresses match the specified postal code.
    """
    data = _get_address_dict_list()
    filtered_data = [
        addr
        for addr in data.get("addresses", [])
        if addr.get("postalCode") == postal_code
    ]
    return random.choice(filtered_data) if filtered_data else {}


def real_random_address_by_city(city: str) -> Dict[str, Any]:
    """Retrieve a random real address filtered by US city name.

    Args:
        city (str): Name of the city to filter the addresses by (e.g., 'Newark').

    Returns:
        dict: Dictionary containing random address information matching the
        provided city.

    Example:
        >>> import random_address
        >>> random_address.real_random_address_by_city('Newark')
        {
            'address1': '37600 Sycamore Street',
            'address2': '',
            'city': 'Newark',
            'state': 'CA',
            'postalCode': '94560',
            'coordinates': {'lat': 37.5261943, 'lng': -122.0304698}
        }

        Returns an empty dictionary if no addresses match the specified city.
    """
    data = _get_address_dict_list()
    filtered_data = [
        addr
        for addr in data.get("addresses", [])
        if addr.get("city") and addr.get("city").lower() == city.lower()
    ]
    return random.choice(filtered_data) if filtered_data else {}
