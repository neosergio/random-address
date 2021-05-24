"""
Functions to retrieve a real random address that geocode successfully
"""
import json
import os
import random
import sys


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
