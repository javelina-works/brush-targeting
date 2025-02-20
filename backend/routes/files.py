from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
from backend.config import LOCATIONS_DIR, load_data

router = APIRouter()

# Allowed file types and their respective MIME types
FILE_TYPES = {
    "geojson": "application/geo+json",
    "tiff": "image/tiff",
    "tif": "image/tiff",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg"
}

# [CREATE] map asset file
@router.post("/files/{job_id}/map/upload/{file_name}")
def upload_map_asset(job_id: str, file_name: str, file: UploadFile = File(...)):
    """
    Upload a map asset (GeoJSON) to the map directory for a job with a specified filename.
    """
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    map_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id, "map")
    os.makedirs(map_dir, exist_ok=True)

    file_path = os.path.join(map_dir, file_name)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return JSONResponse(content={"filename": file_name, "path": file_path})


# [READ] Job file
@router.get("/files/{job_id}/{file_name}")
def get_uploaded_file(job_id: str, file_name: str):
    """
    Retrieve a specific uploaded file for a given job.
    This ensures only expected file types (GeoJSON, images) are served.
    """
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id)
    map_dir = os.path.join(job_dir, "map")
    img_dir = os.path.join(job_dir, "orthophoto")
    search_dir = os.path.join(job_dir, "search")
    
    # Search both the job directory and map directory for the requested file
    for directory in [map_dir, img_dir, job_dir, search_dir]:
        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            file_extension = file_name.split(".")[-1].lower()
            mime_type = FILE_TYPES.get(file_extension, "application/octet-stream")
            file_size = os.path.getsize(file_path)

            return FileResponse(
                file_path, 
                media_type=mime_type,
                filename=file_name,
                stat_result=os.stat(file_path),
                headers={
                    "Content-Length": str(file_size), # Browser understands total size
                    "Cache-Control": "public, max-age=86400", # Enable client caching
                }
            )
    
    raise HTTPException(status_code=404, detail="File not found")


# [LIST] all job files
@router.get("/files/{job_id}")
def list_files(job_id: str):
    """
    List all files in a job directory, categorizing them by type.
    """
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id)

    if not os.path.exists(job_dir):
        raise HTTPException(status_code=404, detail="Job directory not found")

    # Categorized file storage
    categorized_files = {"geojson": [], "images": [], "other": []}

    for root, _, filenames in os.walk(job_dir):
        for filename in filenames:
            file_extension = filename.split(".")[-1].lower()

            if file_extension in ["geojson"]:
                categorized_files["geojson"].append(filename)
            elif file_extension in ["tiff", "png", "jpg", "jpeg"]:
                categorized_files["images"].append(filename)
            else:
                categorized_files["other"].append(filename)

    return JSONResponse(content=categorized_files)
