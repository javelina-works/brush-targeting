from fastapi import APIRouter, HTTPException
import os
import uuid
from backend.models.locations import Job, JobCreate
from backend.config import LOCATIONS_DIR, DATA_FILE, save_data, load_data

router = APIRouter()


# [CREATE] a job linked to a location
@router.post("/jobs/", response_model=Job)
def create_job(new_job: JobCreate):
    data = load_data()

    # Validate location exists
    if not any(loc["id"] == new_job.location_id for loc in data["locations"]):
        raise HTTPException(status_code=404, detail="Location not found")

    job = Job(id=str(uuid.uuid4()), location_id=new_job.location_id, name=new_job.name)
    data["jobs"].append(job.model_dump())
    save_data(data)

    # Create directory for this job inside its location
    job_path = os.path.join(LOCATIONS_DIR, job.location_id, job.id)
    os.makedirs(job_path, exist_ok=True)

    return job


# [UPDATE] a job (rename or move to another location)
@router.put("/jobs/{job_id}", response_model=Job)
def update_job(job_id: str, job: JobCreate):
    data = load_data()
    job_entry = next((j for j in data["jobs"] if j["id"] == job_id), None)

    if not job_entry:
        raise HTTPException(status_code=404, detail="Job not found")

    # Validate new location exists if moving the job
    if job.location_id and not any(loc["id"] == job.location_id for loc in data["locations"]):
        raise HTTPException(status_code=404, detail="New location not found")

    # Update job fields
    job_entry["name"] = job.name
    job_entry["location_id"] = job.location_id

    save_data(data)
    return job_entry


# [DELETE] a job
@router.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    data = load_data()

    # Find job
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Remove job from list
    data["jobs"] = [j for j in data["jobs"] if j["id"] != job_id]
    save_data(data)

    # Remove job directory
    job_path = os.path.join(LOCATIONS_DIR, job["location_id"], job_id)
    if os.path.exists(job_path):
        os.rmdir(job_path)

    return {"message": "Job deleted"}


# [LIST] jobs
@router.get("/jobs/")
def list_jobs(location_id: str = None):
    data = load_data()
    if location_id:
        return [job for job in data["jobs"] if job["location_id"] == location_id]
    return data["jobs"]
