import json

def json_architecture(data, max_list_items=1):
    if isinstance(data, dict):
        return {k: json_architecture(v, max_list_items) for k, v in data.items()}
    elif isinstance(data, list):
        return [json_architecture(data[0], max_list_items)] if data else []
    else:
        return None  # strip values

# Example usage:
with open("results/2b264f744ccebb6145eae69c0b46fef5.json") as f:
    raw = json.load(f)

architecture = json_architecture(raw)

print(json.dumps(architecture, indent=2))
