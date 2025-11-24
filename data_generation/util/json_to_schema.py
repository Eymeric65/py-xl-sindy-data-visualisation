import json
import sys

counter = 0 

def trim_floats(obj):
    if isinstance(obj, dict):
        # Filter out keys that match certain patterns
        filtered_dict = {}
        for k, v in obj.items():
            # Skip if key is a string and meets any of these conditions:
            # - ends with 'id' (case insensitive)
            # - longer than 30 characters
            # - contains '_' or '-' and is longer than 15 characters
            global counter
            
            if isinstance(k, str):
                if len(k) > 30:
                    counter += 1
                    if counter > 1:
                        continue
            
            # Recursively process the value
            filtered_dict[k] = trim_floats(v)
        
        return filtered_dict
    elif isinstance(obj, list):
        # Check if list is not empty and contains only numbers (floats/ints)

        return obj[:5] # Slice to max 5 items

    return obj

# Read from stdin, process, and print to stdout
if __name__ == "__main__":
    try:
        data = json.load(sys.stdin)
        print(json.dumps(trim_floats(data), indent=2))
    except json.JSONDecodeError:
        print("Invalid JSON input", file=sys.stderr)