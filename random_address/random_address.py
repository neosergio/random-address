"""
Functions to retrieve a real random address that geocode successfully
"""

import json
import logging
import os
import random
import sys
from typing import Any, Dict, List
from collections import Counter

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


def list_available_states() -> List[str]:
    """Get a sorted list of all unique US state codes in the dataset.

    Returns:
        List[str]: Alphabetically sorted list of unique state codes.
    """
    data = _get_address_dict_list()
    return sorted({addr.get("state") for addr in data.get("addresses", []) if addr.get("state")})


def list_available_postal_codes() -> List[str]:
    """Get a sorted list of all unique postal codes in the dataset.

    Returns:
        List[str]: Alphabetically sorted list of unique postal codes.
    """
    data = _get_address_dict_list()
    return sorted({addr.get("postalCode") for addr in data.get("addresses", []) if addr.get("postalCode")})


def list_available_cities() -> List[str]:
    """Get a sorted list of all unique city names in the dataset.

    Returns:
        List[str]: Alphabetically sorted list of unique cities.
    """
    data = _get_address_dict_list()
    return sorted({addr.get("city") for addr in data.get("addresses", []) if addr.get("city")})


def list_states_with_counts() -> Dict[str, int]:
    """Get a dictionary of all state codes with their corresponding address counts.

    Returns:
        Dict[str, int]: Dictionary with state codes as keys and counts as values.
    """
    data = _get_address_dict_list()
    states = [addr.get("state") for addr in data.get("addresses", []) if addr.get("state")]
    return dict(Counter(states))


def list_postal_codes_with_counts() -> Dict[str, int]:
    """Get a dictionary of all postal codes with their corresponding address counts.

    Returns:
        Dict[str, int]: Dictionary with postal codes as keys and counts as values.
    """
    data = _get_address_dict_list()
    postals = [addr.get("postalCode") for addr in data.get("addresses", []) if addr.get("postalCode")]
    return dict(Counter(postals))


def list_cities_with_counts() -> Dict[str, int]:
    """Get a dictionary of all city names with their corresponding address counts.

    Returns:
        Dict[str, int]: Dictionary with city names as keys and counts as values.
    """
    data = _get_address_dict_list()
    cities = [addr.get("city") for addr in data.get("addresses", []) if addr.get("city")]
    return dict(Counter(cities))


def get_summary() -> Dict[str, Any]:
    """Get a summary of the address dataset.

    Returns:
        Dict[str, Any]: Dictionary summarizing number of addresses, states, cities, and postal codes.
    """
    data = _get_address_dict_list()
    addresses = data.get("addresses", [])
    return {
        "total_addresses": len(addresses),
        "unique_states": len({addr.get("state") for addr in addresses if addr.get("state")}),
        "unique_cities": len({addr.get("city") for addr in addresses if addr.get("city")}),
        "unique_postal_codes": len({addr.get("postalCode") for addr in addresses if addr.get("postalCode")}),
    }
