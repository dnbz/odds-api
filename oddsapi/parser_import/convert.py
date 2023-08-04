def convert_object_key_totals(event) -> dict:
    """Converts objects where totals are object keys to where totals are object values."""
    result = []
    for key, value in event.total_odds.items():
        value["total"] = key
        result.append(value)

    event.total_odds = result

    return event
