import json

with open("addresses-us-all.json", encoding="utf-8") as file:
    data = json.load(file)

with open("addresses-us-all.min.json", "w", encoding="utf-8") as file:
    json.dump(data, file, separators=(",", ":"))
