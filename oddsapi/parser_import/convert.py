def convert_object_key_totals(event) -> dict:
    """Converts objects where totals are object keys to where totals are object values."""
    # if not dict - quit
    if not isinstance(event.first_half_total_odds, dict):
        return event

    result = []
    for key, value in event.total_odds.items():
        value["total"] = key
        result.append(value)

    event.total_odds = result

    return event


def convert_object_key_first_half_totals(event) -> dict:
    """Converts objects where totals are object keys to where totals are object values."""
    # if not dict - quit
    if not isinstance(event.first_half_total_odds, dict):
        return event

    result = []
    for key, value in event.first_half_total_odds.items():
        value["total"] = key
        result.append(value)

    event.first_half_total_odds = result

    return event
