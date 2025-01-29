from .vegetation_indices import calculate_exg, normalize_rgb
from skimage.exposure import equalize_adapthist
from skimage.morphology import opening, closing, disk
from skimage.filters import threshold_otsu
from skimage.measure import label, regionprops
import cv2
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon


def generate_target_mask(image):

    # Normalize ExG to the range [0, 255] for OpenCV compatibility
    exg = calculate_exg(*normalize_rgb(image))
    exg_normalized = (exg - np.min(exg)) / (np.max(exg) - np.min(exg))  # Normalize to [0, 1]
    exg_uint8 = (exg_normalized * 255).astype(np.uint8)


    # Step 1: Bilateral Filtering using OpenCV
    bl_sigma_color = 50
    bl_sigma_spatial = 15 # Lower number is faster

    bilateral_smoothed_exg = cv2.bilateralFilter(
        exg_uint8 , d=9, 
        sigmaColor=bl_sigma_color, 
        sigmaSpace=bl_sigma_spatial
    )
    bilateral_smoothed_exg = bilateral_smoothed_exg / 255.0  # Scale back to [0, 1]

    # Step 2: Contrast Enhancement with CLAHE
    clahe_exg = equalize_adapthist(bilateral_smoothed_exg, clip_limit=0.008)

    # Step 3: Morphological Operations (Opening → Closing)
    selem = disk(7)  # Structuring element
    morph_exg = closing(opening(clahe_exg, selem), selem)

    # Step 4: Thresholding (Otsu's method)
    otsu_threshold = threshold_otsu(morph_exg)
    binary_mask = morph_exg > otsu_threshold

    return binary_mask

def correct_binary_mask(binary_mask, original_shape):
    """
    Correct the binary mask by upscaling it to match the original image's resolution.

    Parameters:
    - binary_mask: ndarray
        The downsampled binary mask.
    - original_shape: tuple
        The shape of the original image (height, width).

    Returns:
    - corrected_mask: ndarray
        The binary mask scaled back to the original resolution.
    """
    # Upscale the binary mask to match the original dimensions
    upscaled_mask = cv2.resize(binary_mask.astype(np.uint8), 
                               (original_shape[1], original_shape[0]),  # width, height
                               interpolation=cv2.INTER_NEAREST)

    # Threshold to ensure binary values (0 or 1)
    corrected_mask = (upscaled_mask > 0).astype(np.uint8)

    return corrected_mask

def identify_targets(binary_mask, transform, region_crs="EPSG:32613"):
    # Step 1: Preprocess the binary mask
    selem = disk(3)  # Structuring element
    cleaned_mask = closing(binary_mask, selem)  # Fill small gaps

    # Step 2: Label connected components
    labeled_mask = label(cleaned_mask)
    regions = regionprops(labeled_mask)

    # Step 3: Extract centroids and bounding boxes
    features = []

    for region in regions:
        # Centroid (convert pixel coordinates to geographic coordinates)
        centroid_row, centroid_col = region.centroid  # (row, col in pixel space)
        centroid_x, centroid_y = transform * (centroid_col, centroid_row)  # Apply affine transform
        centroid_point = Point(centroid_x, centroid_y)  # Geographic centroid as Point

        # Bounding box
        min_row, min_col, max_row, max_col = region.bbox
        min_x, min_y = transform * (min_col, min_row)  # Top-left corner
        max_x, max_y = transform * (max_col, max_row)  # Bottom-right corner
        bounding_box = Polygon([
            (min_x, min_y),
            (max_x, min_y),
            (max_x, max_y),
            (min_x, max_y),
            (min_x, min_y)  # Close the polygon
        ])

        # Add to feature list
        features.append({"geometry": centroid_point, "bounding_box": bounding_box})

    # Step 4: Create GeoDataFrame
    targets_gdf = gpd.GeoDataFrame(features, crs=region_crs)

    return targets_gdf


import uuid

def assign_target_metadata(targets_gdf, region_name, region_version):
    """
    Assigns a globally unique ID to each target in `targets_gdf` and associates an outline version.

    Parameters:
    - targets_gdf (GeoDataFrame): The GeoDataFrame containing target points.
    - region_name (str): Name of region for which we have an outline.
    - region_version (str): The outline version to associate with each target.

    Returns:
    - GeoDataFrame: Updated `targets_gdf` with unique IDs and version.
    """
    # Assign a globally unique ID to each target
    targets_gdf["target_id"] = [str(uuid.uuid4()) for _ in range(len(targets_gdf))]

    # Associate each target with the given outline version
    targets_gdf["region_outline_version"] = region_version
    targets_gdf["region_name"] = region_name

    return targets_gdf
