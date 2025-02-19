from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import cv2
import numpy as np
from backend.models.locations import Job
from backend.config import ( 
    LOCATIONS_DIR, DATA_FILE, load_data, save_data, 
    REGION_FILE, REGION_ORTHOPHOTO, REGION_ORTHOPHOTO_PNG
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
async def upload_orthophoto(job_id: str, file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".tif", ".tiff", ".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Invalid file type for orthophoto")
    
    file_bytes = await file.read() # raw image file bytes

    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    img_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id, "orthophoto")
    os.makedirs(img_dir, exist_ok=True)
    
    file_path = os.path.join(img_dir, REGION_ORTHOPHOTO)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    png_path = os.path.join(img_dir, REGION_ORTHOPHOTO_PNG)
    image_array = np.frombuffer(file_bytes, np.uint8) # Convert from bytes to NumPy array
    tif_image = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)  # Decode TIFF image
    if tif_image is None:
        raise HTTPException(status_code=500, detail="Failed to read TIFF file")
    cv2.imwrite(str(png_path), tif_image)  # Save as PNG
    
    job["orthophoto_path"] = file_path
    job["orthophoto_png_path"] = png_path
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