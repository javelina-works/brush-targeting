import os
import json
# import geopandas as gpd
from backend.config import LOCATIONS_DIR, DATA_FILE, load_data, save_data

def ensure_audit_files(job_path):
    """
    Helper function to `fetch_map_assets`, 
    """
       # Ensure `approved_targets.geojson` and `removed_targets.geojson` exist
    targets_path = os.path.join(job_path, "targets.geojson")
    approved_targets_path = os.path.join(job_path, "approved_targets.geojson")
    removed_targets_path = os.path.join(job_path, "removed_targets.geojson")

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

            assets.append({
                "id": layer_name,  # Using filename as the ID
                "name": layer_name,  # Layer name from file
                "type": "GeoJSON",
                "geojson": json.dumps(geojson_data)  # Store as string
            })

    return assets
