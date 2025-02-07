from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import json
from backend.models.locations import Job
from backend.config import LOCATIONS_DIR, DATA_FILE, load_data, save_data

router = APIRouter()

@router.post("/upload/{job_id}")
def upload_image(job_id: str, file: UploadFile = File(...)):
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    file_path = os.path.join(LOCATIONS_DIR, job["location_id"], job_id, f"{job_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    job["input_image_path"] = file_path
    save_data(data)

    return {"filename": file.filename, "path": file_path}
