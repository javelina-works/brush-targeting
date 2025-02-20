import os
import tempfile
import shutil
import subprocess
import re
import rasterio
from rasterio.enums import Resampling
from rio_cogeo.cogeo import cog_translate, cog_validate
from rio_cogeo.profiles import cog_profiles
from pathlib import Path

from backend.config import logger

# Much of this good work is directly taken from WebODM:
#   https://github.com/OpenDroneMap/WebODM/blob/master/app/cogeo.py#L90

def valid_cogeo(src_path):
    """
    Validate a Cloud Optimized GeoTIFF
    :param src_path: path to GeoTIFF
    :return: true if the GeoTIFF is a cogeo, false otherwise
    """
    try:
        from backend.vendor.validate_cloud_optimized_geotiff import validate
        warnings, errors, details = validate(src_path, full_check=True)
        return not errors and not warnings
    except ModuleNotFoundError:
        logger.warning("Using legacy cog_validate (osgeo.gdal package not found)")
        # Legacy
        return cog_validate(src_path, strict=True)


def assure_cogeo(src_path):
    """
    Guarantee that the .tif passed as an argument is a Cloud Optimized GeoTIFF (cogeo)
    If the path is not a cogeo, it is destructively converted into a cogeo.
    If the file cannot be converted, the function does not change the file
    :param src_path: path to GeoTIFF (cogeo or not)
    :return: None
    """

    if not os.path.isfile(src_path):
        logger.warning("Cannot validate cogeo: %s (file does not exist)" % src_path)
        return

    if valid_cogeo(src_path):
        return

    # Not a cogeo
    logger.info("Optimizing %s as Cloud Optimized GeoTIFF" % src_path)

    # Check if we have GDAL >= 3.1
    use_legacy = False
    gdal_version = get_gdal_version()
    if gdal_version:
        major, minor, build = gdal_version
        
        # GDAL 2 and lower
        if major <= 2:
            use_legacy = True
        
        # GDAL 3.0 and lower
        if major == 3 and minor < 1:
            use_legacy = True
    else:
        # This shouldn't happen
        use_legacy = True
        
    if use_legacy:
        logger.warning("Using legacy implementation (GDAL >= 3.1 not found)")
        return make_cogeo_legacy(src_path)
    else:
        return make_cogeo_gdal(src_path)

def get_gdal_version():
    # Bit of a hack without installing 
    # python bindings
    gdal_translate = shutil.which('gdal_translate')
    if not gdal_translate:
        return None
    
    # Get version
    version_output = subprocess.check_output([gdal_translate, "--version"]).decode('utf-8')
    
    m = re.match(r"GDAL\s+([\d+])\.([\d+])\.([\d+]),\s+released", version_output)
    if not m:
        return None
    
    return tuple(map(int, m.groups()))


def convert_to_cog_rio(input_path: Path, output_path: Path):
    """
    Converts a regular GeoTIFF to a Cloud-Optimized GeoTIFF (COG)
    using WebODM-style optimizations and tempfiles.
    """
    config = dict(
        BLOCKSIZE=256,  # Optimized for tile serving
        COMPRESS="DEFLATE",  # Lossless compression
        OVERVIEWS=[2, 4, 8, 14, 16, 19, 20, 21],  # Multi-level pyramid for fast zooming
        OVERVIEW_RESAMPLING=Resampling.nearest.name,  # Use nearest for quick access
    )

    profile = cog_profiles.get("deflate")

    # Use a temporary file for safe processing
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp_file:
        temp_output = Path(tmp_file.name)

    try:
        # Convert to COG using temporary file
        cog_translate(
            str(input_path),
            str(temp_output),
            profile,
            config=config,
            use_cog_driver=True,
        )

        # Validate the COG before moving it to final location
        if not valid_cogeo(temp_output):
            raise ValueError("❌ COG validation failed! The file is not a valid COG.")

        # Move the temp file to the final destination
        temp_output.rename(output_path)

        print(f"✅ COG successfully created: {output_path}")
    
    except Exception as e:
        logger.error(f"❌ COG conversion failed: {e}")
        temp_output.unlink(missing_ok=True)  # Remove the temp file if conversion fails
        raise
