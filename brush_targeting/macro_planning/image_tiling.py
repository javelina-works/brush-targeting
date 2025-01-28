from rio_tiler.io import COGReader
from rio_tiler.profiles import img_profiles
from rio_tiler.errors import TileOutsideBounds
import os
from threading import Thread
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reproject_to_crs(input_path, output_path, target_crs="EPSG:4326"):
    """
    Reproject a GeoTIFF to a specified CRS if it is not already in that CRS.

    Parameters:
    - input_path (str): Path to the input GeoTIFF.
    - output_path (str): Path to save the reprojected GeoTIFF.
    - target_crs (str): Target CRS in EPSG format (default is EPSG:4326).

    Returns:
    - str: Path to the reprojected or original GeoTIFF.
    """
    with rasterio.open(input_path) as src:
        # Check if the source CRS matches the target CRS
        if str(src.crs) == target_crs:
            print(f"GeoTIFF is already in the target CRS ({target_crs}). Skipping reprojection.")
            return input_path

        # Reproject the GeoTIFF to the target CRS
        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update({
            "crs": target_crs,
            "transform": transform,
            "width": width,
            "height": height
        })

        with rasterio.open(output_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest
                )

    print(f"Reprojected GeoTIFF saved to {output_path}")
    return output_path


def start_tile_server(app, host="0.0.0.0", port=8000):
    """
    Start a FastAPI tile server in a separate thread.

    Parameters:
    - app (FastAPI): FastAPI application instance.
    - host (str): Host to bind the server.
    - port (int): Port to run the server.
    """
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)

    thread = Thread(target=server.run, daemon=True)
    thread.start()
    print(f"Tile server running at http://{host}:{port}/{{z}}/{{x}}/{{y}}.png")


def create_tile_server_in_notebook(geotiff_path):
    """
    Create and start a tile server from a GeoTIFF within a Jupyter notebook.

    Parameters:
    - geotiff_path (str): Path to the reprojected GeoTIFF.
    """
    app = FastAPI()

    @app.get("/{z}/{x}/{y}.png")
    async def tile(z: int, x: int, y: int):
        try:
            with COGReader(geotiff_path) as cog:
                tile_data, _ = cog.tile(x, y, z)
                tile_path = f"tile_{z}_{x}_{y}.png"
                cog.write_tile(tile_data, tile_path, img_format="png", profile=img_profiles["png"])
                return FileResponse(tile_path)
            
        except TileOutsideBounds:
            # Create a transparent PNG for out-of-bounds tiles
            transparent_tile = "transparent_tile.png"
            if not os.path.exists(transparent_tile):
                from PIL import Image
                img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))  # 256x256 transparent tile
                img.save(transparent_tile)
            return FileResponse(transparent_tile)
        
        except Exception as e:
            logger.error(f"Error generating tile: {e}")
            raise

    return app

def create_tile_server(geotiff_path, port=8000):
    """
    Create a tile server for the GeoTIFF using FastAPI.

    Parameters:
    - geotiff_path (str): Path to the reprojected GeoTIFF.
    - port (int): Port to run the FastAPI server.
    """
    app = FastAPI()

    @app.get("/{z}/{x}/{y}.png")
    async def tile(z: int, x: int, y: int):
        try:
            with COGReader(geotiff_path) as cog:
                tile_data, _ = cog.tile(x, y, z)
                tile_path = f"tile_{z}_{x}_{y}.png"
                cog.write_tile(tile_data, tile_path, img_format="png", profile=img_profiles["png"])
                return FileResponse(tile_path)
        except TileOutsideBounds:
            # Create a transparent PNG for out-of-bounds tiles
            transparent_tile = "transparent_tile.png"
            if not os.path.exists(transparent_tile):
                from PIL import Image
                img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))  # 256x256 transparent tile
                img.save(transparent_tile)
            return FileResponse(transparent_tile)
        except Exception as e:
            logger.error(f"Error generating tile: {e}")
            raise

    uvicorn.run(app, host="0.0.0.0", port=port)


def tile_and_serve_geotiff(input_geotiff, port=8000):
    """
    Full pipeline to reproject, tile, and serve a GeoTIFF for ipyleaflet.

    Parameters:
    - input_geotiff (str): Path to the input GeoTIFF.
    - port (int): Port to serve tiles.
    """
    # Reproject the GeoTIFF to EPSG:3857
    reprojected_path = "reprojected.tif"
    reproject_to_crs(input_geotiff, reprojected_path)

    # Serve tiles
    create_tile_server(reprojected_path, port)


