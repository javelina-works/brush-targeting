import os
import json

# Base directory for all storage
BASE_DIR = "backend/media"

# Directory where location folders will be stored
LOCATIONS_DIR = os.path.join(BASE_DIR, "locations")

# Path to the locations.json data file
DATA_FILE = os.path.join(BASE_DIR, "locations.json")

# Ensure required directories exist
os.makedirs(LOCATIONS_DIR, exist_ok=True)  # Creates 'backend/media/locations'
os.makedirs(BASE_DIR, exist_ok=True)  # Ensures 'backend/media' exists

# Ensure locations.json exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        f.write('{"locations": [], "jobs": []}')  # Initialize empty JSON

# Load data from JSON
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Save data to JSON
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
