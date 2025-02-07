from fastapi import APIRouter, HTTPException
import json
import os
import uuid
from backend.models.locations import Location, Job
from backend.config import LOCATIONS_DIR, DATA_FILE 

router = APIRouter()


# Ensure data file exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"locations": [], "jobs": []}, f)

# Load data from JSON
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Save data to JSON
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Create a location
@router.post("/locations/", response_model=Location)
def create_location(name: str):
    data = load_data()
    location = Location(id=str(uuid.uuid4()), name=name)
    data["locations"].append(location.model_dump())
    save_data(data)

    # Create directory for this location
    # location_path = os.path.join(LOCATIONS_DIR, location.id)
    # os.makedirs(location_path, exist_ok=True)

    return location

# List locations
@router.get("/locations/")
def list_locations():
    data = load_data()
    return data["locations"]


# Create a job linked to a location
@router.post("/jobs/", response_model=Job)
def create_job(location_id: str, name: str):
    data = load_data()

    # Validate location exists
    if not any(loc["id"] == location_id for loc in data["locations"]):
        raise HTTPException(status_code=404, detail="Location not found")

    job = Job(id=str(uuid.uuid4()), location_id=location_id, name=name)
    data["jobs"].append(job.model_dump())
    save_data(data)

    # Create directory for this job inside its location
    job_path = os.path.join(LOCATIONS_DIR, location_id, job.id)
    os.makedirs(job_path, exist_ok=True)

    return job

# List jobs
@router.get("/jobs/")
def list_jobs(location_id: str = None):
    data = load_data()
    if location_id:
        return [job for job in data["jobs"] if job["location_id"] == location_id]
    return data["jobs"]
