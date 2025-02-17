from fastapi import APIRouter, UploadFile, Query, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, Response
from pathlib import Path
import asyncio
import os
import rasterio
from rasterio.enums import Compression
from rio_tiler.io import Reader
from rio_tiler.profiles import img_profiles
from rio_tiler.errors import TileOutsideBounds
from backend.config import ( 
    LOCATIONS_DIR, DATA_FILE, load_data, save_data, 
    REGION_FILE, REGION_ORTHOPHOTO, REGION_COG
)

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
    if not image_path.exists():
        raise FileNotFoundError(f"Image file {image_path} not found for job {job_id}.")

    return image_path


# Async generator function to stream progress updates
async def generate_tiles_stream(image_path: str, output_dir: str, tile_size: int, min_zoom: int, max_zoom: int):
    try:
        
        with COGReader(image_path) as cog:
            total_tiles = sum(2 ** (2 * z) for z in range(min_zoom, max_zoom + 1))
            completed = 0

            for z in range(min_zoom, max_zoom + 1):
                for x in range(2**z):
                    for y in range(2**z):
                        try:
                            tile, mask = tile_read(image_path, x, y, z, tilesize=tile_size)

                            tile_path = output_dir / f"{z}/{x}/{y}.png"
                            tile_path.parent.mkdir(parents=True, exist_ok=True)

                            with rasterio.open(
                                tile_path, "w", driver="PNG",
                                width=tile.shape[1], height=tile.shape[2],
                                count=tile.shape[0], dtype=tile.dtype.name
                            ) as dst:
                                dst.write(tile)

                            completed += 1
                            yield f"data: {completed}/{total_tiles}\n\n"

                            await asyncio.sleep(0.05)  # Simulated delay for streaming
                        except Exception:
                            pass

        yield "data: complete\n\n"

    except FileNotFoundError as e:
        yield f"data: error: {str(e)}\n\n"


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

    # [3] Return streaming response for progress updates
    return StreamingResponse(
        generate_tiles_stream(str(image_path), str(tile_dir), tile_size, min_zoom, max_zoom),
        media_type="text/event-stream"
    )



# [READ] Serve tiles from a given project
@router.get("/tile/{location_id}/{job_id}/{z}/{x}/{y}.png")
async def get_cog_tile(
    location_id: str, 
    job_id: str, 
    z: int, x: int, y: int, 
    tile_size: int = 256
):
    """ Serves tiles dynamically from a COG """
    cog_path = os.path.join(LOCATIONS_DIR, location_id, job_id, "tiles", REGION_COG)

    if not cog_path.exists():
        logger.warning(f"File not found: {cog_path}")
        return JSONResponse(content={"error": "COG not found"}, status_code=404)

    with Reader(cog_path) as cog:
        tile, mask = cog.tile(x, y, z, tilesize=tile_size)

        # Convert tile to PNG
        img_bytes = cog.render(tile, mask=mask, img_format="PNG")
        return Response(content=img_bytes, media_type="image/png")