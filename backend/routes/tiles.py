from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, Response
from pathlib import Path
import os
from io import BytesIO
from PIL import Image
from rio_tiler.io import Reader
from rio_tiler.errors import TileOutsideBounds
from backend.config import ( 
    LOCATIONS_DIR, DATA_FILE, load_data, save_data, 
    REGION_FILE, REGION_ORTHOPHOTO, REGION_COG
)

from backend.services.cogeo import convert_to_cog_rio

# TODO: pull loging into config for app-wide access
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()

TILE_DIR = Path("./tiles")

# Helper function to locate the correct image based on job_id
def get_image_path(job_id: str) -> Path:
    """Finds the image file associated with the given job_id."""

    # [1] Find job for which we are finding image
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job of id {job_id} not found")

    # [2] Retreive region image
    image_path = os.path.join(LOCATIONS_DIR, job["location_id"], job_id, "orthophoto", REGION_ORTHOPHOTO)    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file {image_path} not found for job {job_id}.")

    return image_path


# [GET] URL for dynamic tiling
@router.get("/get_tile_url/")
async def get_tile_url(location_id: str, job_id: str, request: Request):
    """Returns the tile server URL if a COG exists."""
    cog_path = os.path.join(LOCATIONS_DIR, location_id, job_id, "tiles", REGION_COG)
    if not os.path.exists(cog_path):
        return JSONResponse(content={"error": "COG not found"}, status_code=404)

    # Get the base URL from the request
    base_url = str(request.base_url).rstrip("/")

    tile_url = f"{base_url}/api/tile/{location_id}/{job_id}/" + "{z}/{x}/{y}.png"
    return {"tile_url": tile_url}



# [CREATE] tiles for region orthophoto
@router.post("/generate_tiles/{job_id}/")
async def generate_tiles_stream_api(
    job_id: str,
    tile_size: int = Query(256, description="Tile size in pixels"),
    min_zoom: int = Query(15, description="Minimum zoom level"),
    max_zoom: int = Query(21, description="Maximum zoom level"),
):
    """ API to upload an orthophoto and generate tiles while streaming progress """
    # [1] Find job for which we are generating tiles
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # [2] Init tile directory, get input image
    tile_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id, "tiles")
    os.makedirs(tile_dir, exist_ok=True)
    # TODO: clear directory of previous generated tiles, if exist

    image_path = get_image_path(job_id) # Get path for our image
    output_path = os.path.join(tile_dir, REGION_COG)

    # [3] Generate region COG (Cloud-Optomized GeoTiff)
    try:
        # convert_to_cog(image_path, output_path)
        convert_to_cog_rio(image_path, output_path)
    except Exception as e:
        logger.error(f"Failed to create COG: {e}")
        raise HTTPException(status_code=400, detail="COG generation failed!")

    # [3] Return streaming response for progress updates
    return {"message": "COG created successfully", "cog_path": str(output_path)}


# [READ] Serve tiles from a given project
@router.get("/tile/{location_id}/{job_id}/{z}/{x}/{y}.png")
def get_cog_tile(
    location_id: str, 
    job_id: str, 
    z: int, x: int, y: int, 
    tile_size: int = 256
):
# ) -> StreamingResponse | Response:
    """
    Serves tiles dynamically from a COG
    """
    cog_path = os.path.join(LOCATIONS_DIR, location_id, job_id, "tiles", REGION_COG)

    if not os.path.exists(cog_path):
        logger.warning(f"File not found: {cog_path}")
        return JSONResponse(content={"error": "COG not found. Have you already generated tiles?"}, status_code=404)

    try:
        with Reader(cog_path) as cog:
            # tile_image  = cog.tile(x, y, z, tilesize=tile_size)
            # image_blob = tile_image.render(img_format="PNG")
            # buffer = BytesIO(image_blob)
            # buffer.seek(0)
            # return StreamingResponse(buffer, media_type="image/png")

            tile_image = cog.tile(x, y, z, tilesize=tile_size)
            content = tile_image.render(img_format="PNG")
            return Response(content, media_type="image/png")
        
    except TileOutsideBounds as oob:
        # Out of bounds, return a blank tile or a 404
        logger.debug("Out of bounds tile request!")
        blank_img = Image.new('RGBA', (256, 256), (0,0,0,0))
        buffer = BytesIO()
        blank_img.save(buffer, format="PNG")
        buffer.seek(0)
        return StreamingResponse(buffer, media_type='image/png')
    
    except HTTPException as e:
        logger.warning("HTTP exception:", e)
        return None

    except Exception as e:
        logger.error("Error fetching tile:", e)  # Print the error for debugging
        raise