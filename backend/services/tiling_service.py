import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.shutil import copy
from rasterio.enums import Compression
from pathlib import Path


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


def convert_to_cog(input_path: Path, output_path: Path):
    """
    Convert a GeoTIFF to a Cloud-Optimized GeoTIFF (COG). 
    Includes built-in image tiling: https://cogeotiff.github.io/rio-tiler/intro/#rio-tilers-magic-partial-reading
    """
    with rasterio.open(input_path) as src:
        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            tiled=True,
            blockxsize=256,
            blockysize=256,
            compress=Compression.deflate,  # Lossless compression
            BIGTIFF="YES"
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            for i in range(1, src.count + 1):
                dst.write(src.read(i), i)
                dst.set_band_description(i, src.descriptions[i - 1])

