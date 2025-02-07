from fastapi import APIRouter, HTTPException
import os
import uuid
from backend.models.locations import Location, LocationCreate
from backend.config import LOCATIONS_DIR, DATA_FILE, load_data, save_data

router = APIRouter()


# [CREATE] a location
@router.post("/locations/", response_model=Location)
def create_location(location: LocationCreate):
    data = load_data()
    location = Location(id=str(uuid.uuid4()), name=location.name)
    data["locations"].append(location.model_dump())
    save_data(data)

    # Create directory for this location
    location_path = os.path.join(LOCATIONS_DIR, location.id)
    os.makedirs(location_path, exist_ok=True)

    return location


# [UPDATE] a location
@router.put("/locations/{location_id}", response_model=Location)
def update_location(location_id: str, new_location: LocationCreate):
    data = load_data()
    location = next((loc for loc in data["locations"] if loc["id"] == location_id), None)

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    location["name"] = new_location.name  # Update name
    save_data(data)
    return location


# [DELETE] location
@router.delete("/locations/{location_id}")
def delete_location(location_id: str):
    data = load_data()

    # Find location
    location = next((loc for loc in data["locations"] if loc["id"] == location_id), None)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Delete associated jobs
    data["jobs"] = [job for job in data["jobs"] if job["location_id"] != location_id]

    # Remove location
    data["locations"] = [loc for loc in data["locations"] if loc["id"] != location_id]
    save_data(data)

    # Remove directory
    location_path = os.path.join(LOCATIONS_DIR, location_id)
    if os.path.exists(location_path):
        os.rmdir(location_path)

    return {"message": "Location deleted"}


# [LIST] locations
@router.get("/locations/")
def list_locations():
    data = load_data()
    return data["locations"]


