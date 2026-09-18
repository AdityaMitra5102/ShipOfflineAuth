import csv
import json
import os
from datetime import datetime

# Path to the CSV database file
CSV_FILE = os.path.join(os.path.dirname(__file__), "ships.csv")


def _find_all_ships(data):
    """
    Recursively scans the entire JSON structure (no matter how deeply
    nested in dicts or lists) and finds all values belonging to the key 'ship'
    (case-insensitive: 'ship', 'Ship', 'SHIP').
    """
    found_ships = []

    if isinstance(data, dict):
        for key, value in data.items():
            # Match 'ship' regardless of uppercase/lowercase or leading spaces
            if str(key).strip().lower() == "ship":
                if isinstance(value, (str, int, float)) and str(value).strip():
                    found_ships.append(str(value).strip())
                else:
                    # If 'ship' itself contains another nested dict or list
                    found_ships.extend(_find_all_ships(value))
            else:
                # Key is something else (e.g. 'data', 'details') -> keep searching deeper
                found_ships.extend(_find_all_ships(value))

    elif isinstance(data, list):
        # Scan every item inside lists
        for item in data:
            found_ships.extend(_find_all_ships(item))

    return found_ships


def add_to_db(json_data):
    """
    Accepts JSON passed from the backend (dict or JSON string).
    Finds the 'ship' value no matter where it is located in the JSON,
    records the current timestamp, and appends it to the CSV file.
    """
    # Parse raw JSON string if Flask passes a string
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return False
    elif isinstance(json_data, (dict, list)):
        data = json_data
    else:
        return False

    # Recursively find any 'ship' anywhere in the JSON
    ships = _find_all_ships(data)
    if not ships:
        return False

    # Timestamp when this data is saved
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if header needs to be written
    file_exists = os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0

    # Append each found ship with the timestamp
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["ship", "timestamp"])
            file_exists = True

        for ship in ships:
            writer.writerow([ship, timestamp])

    return True


def show_all():
    """
    Reads the CSV file and returns a list of all (ship, timestamp) tuples.
    """
    all_ships = []

    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        return all_ships

    with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header row
        for row in reader:
            if row:
                all_ships.append((row[0], row[1]))

    return all_ships
