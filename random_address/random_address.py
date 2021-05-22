import json
import os
import random
import sys


def real_random_address() -> dict:
    package_directory = os.path.dirname(sys.modules[__name__].__file__)
    source_filename_path = os.path.join(package_directory,
                                        'addresses-us-all.min.json')
    source_filename = open(source_filename_path)
    data = json.load(source_filename)
    return random.choice(data.get('addresses'))
