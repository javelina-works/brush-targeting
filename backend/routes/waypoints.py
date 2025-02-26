from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse, StreamingResponse
import os
import zipfile
import json
import zipfly
import io
import geopandas as gpd

from backend.config import LOCATIONS_DIR, load_data, MICRO_ROUTES_FILE

router = APIRouter()

def get_job_directory(job_id: str):
    """Retrieve the directory for a given job ID."""
    # Ensure job existzs
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Ensure job file directory exists
    job_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id)
    if not os.path.exists(job_dir):
        raise HTTPException(status_code=404, detail="No files found for this job")
    
    # Make waypoints directory if needed
    waypoints_dir = os.path.join(job_dir, "waypoints")
    os.makedirs(waypoints_dir, exist_ok=True)
    
    return job_dir, waypoints_dir


def save_routes_as_waypoints_from_geojson(geojson_path, output_dir):
    """
    Save routes as .waypoints files for Mission Planner using a GeoJSON file.

    Parameters:
    - geojson_path (str): Path to the GeoJSON file containing routes.
    - output_dir (str): Path to store .waypoints files.
    """
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(geojson_path, 'r') as f:
            geojson_data = json.load(f)
    except Exception as err:
        print("Unable to read geojson data: {err}")
        raise HTTPException(status_code=400, detail="Unreadable routes file")

    # Ensure GeoJSON has the necessary structure
    if "features" not in geojson_data:
        raise HTTPException(status_code=400, detail="Invalid GeoJSON format")

    for feature in geojson_data["features"]:
        properties = feature.get("properties", {})
        route_id = properties.get("route_id", "unnamed_route")
        geometry = feature.get("geometry", {})

        if geometry.get("type") not in ["LineString", "MultiLineString"]:
            print(f"Skipping unsupported geometry type {geometry.get('type')} for {route_id}")
            continue

        # Extract waypoints
        waypoints = []
        if geometry["type"] == "LineString":
            waypoints = geometry["coordinates"]
        elif geometry["type"] == "MultiLineString":
            for line in geometry["coordinates"]:
                waypoints.extend(line)

        # Convert to Mission Planner .waypoints format
        waypoint_lines = ["QGC WPL 110"]  # Mission Planner header
        # Format: index, current, coord_frame, command, param1, param2, param3, param4, lat, lon, alt, autocontinue
        for i, (lon, lat) in enumerate(waypoints, start=1):
            waypoint_lines.append(f"{i}\t0\t3\t16\t0\t0\t0\t0\t{lat:.6f}\t{lon:.6f}\t10\t1")

        # Save as .waypoints file
        file_path = os.path.join(output_dir, f"{route_id}.waypoints")
        with open(file_path, 'w') as f:
            f.write('\n'.join(waypoint_lines))
        # print(f"Saved {route_id} as {file_path}")

    
@router.get("/waypoints/{job_id}/generate")
def generate_waypoints(job_id: str):
    """
    Generates waypoints from stored routes and saves them in waypoints/.
    """
    job_dir, waypoints_dir = get_job_directory(job_id)

    # Path to micro routes GeoJSON
    routes_file = os.path.join(job_dir, "map", MICRO_ROUTES_FILE)
    if not os.path.exists(routes_file):
        raise HTTPException(status_code=404, detail="Routes file not found")

    save_routes_as_waypoints_from_geojson(routes_file, waypoints_dir)
    return {"message": "Waypoints generated successfully", "path": waypoints_dir}


@router.get("/waypoints/{job_id}/download")
def download_waypoints(job_id: str):
    """Returns a ZIP file of all waypoints for a given job."""
    _, waypoints_dir = get_job_directory(job_id)

    # Ensure waypoints exist
    waypoints_files = [f for f in os.listdir(waypoints_dir) if f.endswith(".waypoints")]
    if not waypoints_files:
        raise HTTPException(status_code=404, detail="No waypoints available")

    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in waypoints_files:
            zip_file.write(os.path.join(waypoints_dir, file), arcname=file)

    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer, 
        media_type="application/zip",
        headers = {
            "Content-Disposition": f"attachment; filename={job_id}_waypoints.zip"
        }
    )