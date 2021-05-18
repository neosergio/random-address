import json
import os
import random


def real_random_address() -> dict:
    package_directory = os.path.dirname(os.path.abspath(__file__))
    source_filename_path = os.path.join(package_directory,
                                        'addresses-us-all.json')
    source_filename = open(source_filename_path)
    data = json.load(source_filename)
    return random.choice(data.get('addresses'))
