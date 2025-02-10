import os
import json
from backend.config import LOCATIONS_DIR, DATA_FILE, load_data, save_data

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
