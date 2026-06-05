import json

def transform_payload(topic: str, payload_str: str) -> dict:
    """
    Parses the MQTT payload and flattens/transforms it into a standard dictionary.
    Handles json.dumps for drop_oscillation and flattens nested dicts where necessary.
    """
    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        return {}

    # Extract topic base name (e.g. drop_oscillation from aut/SoSe26/.../drop_oscillation)
    topic_parts = topic.split('/')
    event_type = topic_parts[-1] if len(topic_parts) > 0 else "unknown"

    transformed = {
        "event_type": event_type,
    }

    # Iterate over the items in the original data and transform specific fields
    for key, value in data.items():
        if key == "drop_oscillation" and isinstance(value, list):
            # The assignment mentions saving this list as a JSON string in CSV
            transformed["drop_oscillation"] = json.dumps(value)
        elif key == "color_levels_grams" and isinstance(value, dict):
            transformed["color_levels_grams"] = json.dumps(value)
        elif key == "vibration-index":
            transformed["vibration_index"] = value # Convert hyphen to underscore for convenience
        else:
            transformed[key] = value

    return transformed
