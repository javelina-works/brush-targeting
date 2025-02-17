from fastapi import APIRouter, UploadFile, File, HTTPException
import os
from backend.models.locations import Job
from backend.config import ( 
    LOCATIONS_DIR, DATA_FILE, load_data, save_data, 
    REGION_FILE, REGION_ORTHOPHOTO
)

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


@router.post("/upload/{job_id}/orthophoto")
def upload_orthophoto(job_id: str, file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".tif", ".tiff", ".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Invalid file type for orthophoto")
    
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    img_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id, "orthophoto")
    os.makedirs(img_dir, exist_ok=True)
    
    file_path = os.path.join(img_dir, REGION_ORTHOPHOTO)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    
    job["orthophoto_path"] = file_path
    save_data(data)
    
    return {"filename": REGION_ORTHOPHOTO, "path": file_path}


@router.post("/upload/{job_id}/region_contour")
def upload_region_outline(job_id: str, file: UploadFile = File(...)):
    print(f"Seaching for job: {job_id}")
    if not file.filename.lower().endswith(".geojson"):
        raise HTTPException(status_code=400, detail="Invalid file type for region outline. Must be .geojson")
    
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    map_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id, "map")
    os.makedirs(map_dir, exist_ok=True)

    file_path = os.path.join(map_dir, REGION_FILE)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    
    job["region_contour_path"] = file_path
    save_data(data)
    
    return {"filename": REGION_FILE, "path": file_path}