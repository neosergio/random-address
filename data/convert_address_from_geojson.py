import json
import random


def convert_geojson_to_json(address) -> dict:
    return {
        "address1": f"{address['properties']['number']} {address['properties']['street']}",
        "address2": f"{address['properties']['unit']}",
        "city": "Arlington",
        "state": "VA",
        "postalCode": address['properties']['postcode'],
        "coordinates": {
            "lat": address['geometry']['coordinates'][1],
            "lng": address['geometry']['coordinates'][0]
        }
    }


# Load the GeoJSON file and convert it to a list of dictionaries
with open("source.geojson", 'r') as file:
    addresses = [json.loads(line) for line in file.readlines()]

selected = random.sample(addresses, 50)

addresses_converted = [convert_geojson_to_json(address) for address in selected]

with open('addresses.json', 'w') as file:
    json.dump(addresses_converted, file, indent=2)

print(str(len(addresses_converted)) + " converted addresses")
