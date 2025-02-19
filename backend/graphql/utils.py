import os
import json
from typing import Optional, Dict
# import geopandas as gpd
from backend.config import (
    LOCATIONS_DIR, SEARCH_TARGETS_FILE,
    APPROVED_TARGETS_FILE, REMOVED_TARGETS_FILE,
)

def ensure_audit_files(job_path):
    """
    Helper function to `fetch_map_assets`, 
    """
       # Ensure `approved_targets.geojson` and `removed_targets.geojson` exist
    targets_path = os.path.join(job_path, SEARCH_TARGETS_FILE)
    approved_targets_path = os.path.join(job_path, APPROVED_TARGETS_FILE)
    removed_targets_path = os.path.join(job_path, REMOVED_TARGETS_FILE)

    if os.path.exists(targets_path):
        with open(targets_path, "r", encoding="utf-8") as f:
            targets_data = json.load(f)

    # Initialize `approved_targets.geojson` if missing
    if not os.path.exists(approved_targets_path):
        approved_targets = targets_data.copy()  # Copy entire structure
        approved_targets["name"] = "Approved Targets"

        with open(approved_targets_path, "w", encoding="utf-8") as f:
            json.dump(approved_targets, f, indent=4)

    # Initialize `removed_targets.geojson` if missing
    if not os.path.exists(removed_targets_path):
        removed_targets = targets_data.copy()  # Copy entire structure
        removed_targets["features"] = []  # Empty feature list
        removed_targets["name"] = "Removed Targets"

        with open(removed_targets_path, "w", encoding="utf-8") as f:
            json.dump(removed_targets, f, indent=4)


def fetch_map_asset(location_id: str, job_id: str, file_name: str) -> Optional[Dict]:
    """
    Utility function to retrieve a specific file for a given project & job.
    - Supports GeoJSON file retrieval and conversion to a GeoDataFrame.
    """
    job_path = os.path.join(LOCATIONS_DIR, location_id, job_id, "map")
    file_path = os.path.join(job_path, file_name)

    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data # JSON data
    except Exception as e:
        print(f"Error loading {file_name}: {e}")
        return None


def fetch_map_assets(location_id: str, job_id: str):
    """
    Fetches all available map assets (GeoJSON files) for a given location and job.

    - Reads files from `data/{location_id}/{job_id}/`
    - Returns a list of available asset names and their GeoJSON contents.
    """
    assets = []
    job_path = os.path.join(LOCATIONS_DIR, location_id, job_id, "map")
    print(job_path)

    if not os.path.exists(job_path):
        return []  # Return empty if no assets exist for this job

    ensure_audit_files(job_path) # Creates target files if they don't exist
    

    for filename in os.listdir(job_path):
        if filename.endswith(".geojson"):  # Only load GeoJSON files
            layer_name = filename.replace(".geojson", "")  # Strip file extension
            file_path = os.path.join(job_path, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)

            # TODO: should really type this as MapAsset if returning as such
            assets.append({
                "id": layer_name,  # Using filename as the ID
                "name": layer_name,  # Layer name from file
                "type": "GeoJSON",
                "geojson": json.dumps(geojson_data)  # Store as string
            })

    return assets


def save_geojson_file(location_id: str, job_id: str, file_name: str, geojson_data: str) -> bool:
    """
    Saves updated GeoJSON data to disk.
    """
    job_path = os.path.join(LOCATIONS_DIR, location_id, job_id, "map")

    if not os.path.exists(job_path):
        os.makedirs(job_path)  # Ensure the directory exists

    file_path = os.path.join(job_path, f"{file_name}.geojson")

    try:
        # Validate JSON
        parsed_geojson = json.loads(geojson_data)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(parsed_geojson, f, indent=4)

        print(f"✅ Successfully saved {file_name}.geojson")
        return True
    except Exception as e:
        print(f"❌ Error saving {file_name}.geojson:", e)
        return False
    