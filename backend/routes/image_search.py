from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import cv2
import numpy as np
import json
import os
# import geojson
from backend.config import (
    LOCATIONS_DIR, load_data, REGION_ORTHOPHOTO, CV_OUTPUT_FILE, 
    BINARY_MASK, SEARCH_TARGETS_FILE,
)
from backend.services.plant_search.load_image import load_image
from backend.services.plant_search.image_preprocess import (
    preprocess_image, threshold_image, identify_targets, assign_target_metadata
)
from backend.graphql.utils import save_geojson_file


router = APIRouter()

# Base directory for storing job data
BASE_DIR = Path("jobs_data")
BASE_DIR.mkdir(exist_ok=True)


class ThresholdingRequest(BaseModel):
    job_id: str
    threshold: float  # Example: 0.5 for binary thresholding

class TargetGenerationRequest(BaseModel):
    job_id: str

@router.post("/process_cv/{job_id}")
async def process_cv(job_id: str) -> FileResponse:
    """
    Applies CV techniques to the job's orthophoto and saves output.
    """
    # 1) Find job from passed ID
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 2) Find input image, output artifact directories
    job_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job["id"])
    ortho_path = os.path.join(job_dir, "orthophoto", REGION_ORTHOPHOTO)
    if not os.path.exists(ortho_path):
        raise HTTPException(status_code=404, detail="Orthophoto not found")
    
    search_dir = os.path.join(job_dir, "search")
    os.makedirs(search_dir, exist_ok=True)
    output_path = os.path.join(search_dir, CV_OUTPUT_FILE)

    # 3) Load image as NP array
    image, transform, bounds, image_crs = load_image(ortho_path)

    # 4) Perform image thresholding
    processed_image = preprocess_image(image)

    # 5) Save processed image to correct directory
    cv2.imwrite(str(output_path), processed_image)

    return FileResponse(output_path, media_type="image/tif", filename=CV_OUTPUT_FILE)


@router.post("/apply_threshold")
async def apply_threshold(request: ThresholdingRequest):
    """Applies thresholding to the output of process_cv."""

    # 1) Find job from passed ID
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == request.job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 2) Find input image, output artifact directories
    job_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job["id"])
    processed_path = os.path.join(job_dir, "search", CV_OUTPUT_FILE)
    if not os.path.exists(processed_path):
        raise HTTPException(status_code=404, detail="Preprocessed image not found")

    binary_mask_path = os.path.join(job_dir, "search", BINARY_MASK)

    # 3) Peform manual thresholding
    image = cv2.imread(str(processed_path), cv2.IMREAD_GRAYSCALE)
    binary_mask = threshold_image(image, request.threshold)

    # 4) Save image to directory
    cv2.imwrite(str(binary_mask_path), binary_mask)

    # return {"message": "Thresholding applied", "output_path": str(binary_mask_path)}
    return FileResponse(binary_mask_path, media_type="image/tif", filename=BINARY_MASK)



@router.post("/generate_targets/{job_id}")
async def generate_targets(job_id: str):
    """Converts binary mask into a GeoJSON of detected targets."""

    # 1) Find job from passed ID
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 2) Find input image, output artifact directories
    job_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job["id"])
    
    binary_mask_path = os.path.join(job_dir, "search", BINARY_MASK)
    if not os.path.exists(binary_mask_path):
        raise HTTPException(status_code=404, detail="Binary mask not found. Has is been generated?")

    ortho_path = os.path.join(job_dir, "orthophoto", REGION_ORTHOPHOTO)
    if not os.path.exists(ortho_path):
        raise HTTPException(status_code=404, detail="Orthophoto not found. It must be present to find targets.")

    targets_path = os.path.join(job_dir, "map", SEARCH_TARGETS_FILE)

    # 3) Load in original image and binary mask
    image, transform, bounds, image_crs = load_image(ortho_path)
    binary_mask = cv2.imread(str(binary_mask_path), cv2.IMREAD_GRAYSCALE)

    # 4) Perform search for targets
    targets_gdf = identify_targets(binary_mask, transform)
    labeled_targets_gdf = assign_target_metadata(targets_gdf, job["name"], job["id"])
    targets_geojson = labeled_targets_gdf.to_json() # Convert from GDF to geoJSON string

    # 5) Save GeoJSON
    filename = SEARCH_TARGETS_FILE
    if filename.endswith(".geojson"):  # Only load GeoJSON files
        filename = filename.replace(".geojson", "")  # Strip file extension

    success = save_geojson_file(job["location_id"], job["id"], filename, targets_geojson)
    if not success:
        raise ValueError(f"Unable to save generated macro routes")

    return {
        "message": "Targets generated", 
        "geojson_path": str(targets_path),
        "geojson": targets_geojson,    
    }
