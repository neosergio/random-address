import json

with open('addresses-us-all.min.json', 'r') as file:
    data = json.load(file)

with open('addresses-us-all.json', 'w') as file:
    json.dump(data, file, indent=2)
