from fastapi import APIRouter, UploadFile, File, HTTPException
import os
from backend.models.locations import Job
import json

router = APIRouter()

UPLOAD_DIR = "storage/uploads/"
DATA_FILE = "data/locations.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"locations": [], "jobs": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@router.post("/upload/")
def upload_image(job_id: str, file: UploadFile = File(...)):
    data = load_data()

    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    job["input_image_path"] = file_path
    save_data(data)

    return {"filename": file.filename, "path": file_path}
