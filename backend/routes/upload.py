from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import cv2
import zipfile
import shutil
import geopandas as gpd
import numpy as np
from backend.models.locations import Job
from backend.config import ( 
    LOCATIONS_DIR, DATA_FILE, load_data, save_data, 
    REGION_FILE, REGION_ORTHOPHOTO, REGION_ORTHOPHOTO_PNG, PROCESSING_CRS, DISPLAY_CRS
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
async def upload_region_outline(job_id: str, file: UploadFile = File(...)):
    """Handles uploading of region boundary in either GeoJSON or Shapefile (.zip) format."""
    
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    map_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id, "map")
    os.makedirs(map_dir, exist_ok=True)

    file_ext = file.filename.lower().split(".")[-1]
    zip_path = None
    extract_dir = None
    geojson_path = os.path.join(map_dir, REGION_FILE)

    try:
        if file_ext == "geojson":
            # Save the uploaded GeoJSON file
            with open(geojson_path, "wb") as f:
                f.write(file.file.read())

            # Load and check CRS
            gdf = gpd.read_file(geojson_path)
            geojson_path = ensure_crs(gdf, geojson_path)

        elif file_ext == "zip":
            # Save zip file temporarily
            zip_path = os.path.join(map_dir, "region_shapefile.zip")
            with open(zip_path, "wb") as f:
                f.write(await file.read())

            # Extract zip contents
            extract_dir = os.path.join(map_dir, "shapefile_temp")
            os.makedirs(extract_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            # Ensure required shapefile components exist
            required_files = {".shp", ".shx", ".dbf"}
            uploaded_files = {os.path.splitext(f)[1] for f in os.listdir(extract_dir)}

            if not required_files.issubset(uploaded_files):
                raise HTTPException(status_code=400, detail="Missing required Shapefile components (.shp, .shx, .dbf).")

            # Locate the .shp file
            shp_files = [f for f in os.listdir(extract_dir) if f.endswith(".shp")]
            if not shp_files:
                raise HTTPException(status_code=400, detail="No .shp file found in uploaded zip.")

            shp_path = os.path.join(extract_dir, shp_files[0])

            # Convert Shapefile to GeoJSON
            try:
                gdf = gpd.read_file(shp_path)
                geojson_path = ensure_crs(gdf, geojson_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error converting shapefile: {str(e)}")

        else:
            raise HTTPException(status_code=400, detail="Invalid file type. Must be .geojson or .zip (Shapefile).")

        job["region_contour_path"] = geojson_path
        save_data(data)

        return {"filename": REGION_FILE, "path": geojson_path}

    finally:
        # Will always execute on exit from a 'try' block
        #   -> See: https://stackoverflow.com/questions/19805654/python-try-finally-block-returns
        # Cleanup regardless of success or failure
        if extract_dir and os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)  # Removes extracted files
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)  # Deletes the uploaded zip file


def ensure_crs(gdf, geojson_path, target_crs=DISPLAY_CRS):
    """Ensures the CRS is in EPSG:3857 (Web Mercator). Reprojects if needed."""
    
    if gdf.crs is None:
        raise HTTPException(status_code=400, detail="GDF lacks a CRS. Unable to transform.")

    if gdf.crs.to_string() != target_crs:
        print(f"Reprojecting from {gdf.crs} to {target_crs}")
        gdf = gdf.to_crs(target_crs)

    # Save as GeoJSON with correct CRS
    gdf.to_file(geojson_path, driver="GeoJSON")
    return geojson_path