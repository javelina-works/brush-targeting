import os
import json

PROCESSING_CRS = "EPSG:32613"
DISPLAY_CRS = "EPSG:4326"
REGION_FILE = "region_contour.geojson"
VORONOI_FILE = "voronoi_cells.geojson"

# Base directory for all storage
BASE_DIR = "backend/media"

# Directory where location folders will be stored
LOCATIONS_DIR = os.path.join(BASE_DIR, "locations")

# Path to stored files
DATA_FILE = os.path.join(BASE_DIR, "locations.json")
PIPELINES_FILE = os.path.join(BASE_DIR, "pipelines.json")

# Ensure required directories exist
os.makedirs(BASE_DIR, exist_ok=True)  # Ensures 'backend/media' exists
os.makedirs(LOCATIONS_DIR, exist_ok=True)  # Creates 'backend/media/locations'

# Ensure locations.json exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        f.write('{"locations": [], "jobs": []}')  # Initialize empty JSON

# Load data from JSON
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Pipelines Persistence
if not os.path.exists(PIPELINES_FILE):
    with open(PIPELINES_FILE, "w") as f:
        f.write('{"pipelines": []}')  # Ensure pipelines.json exists

def load_pipelines():
    if os.path.exists(PIPELINES_FILE):
        with open(PIPELINES_FILE, "r") as file:
            return json.load(file)
    return {}

def save_pipelines(pipelines):
    with open(PIPELINES_FILE, "w") as file:
        json.dump(pipelines, file, indent=4)