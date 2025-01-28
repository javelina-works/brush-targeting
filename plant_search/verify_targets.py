import json 
import random
import rasterio
from typing import Optional
from shapely.geometry import shape, Point, Polygon, box
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np


def load_geojson(file_path):
    """
    Load a GeoJSON file and extract the first polygon geometry.

    Parameters:
        file_path (str): Path to the GeoJSON file.
    
    Returns:
        dict: A GeoJSON Feature with a 'geometry' key.
    """
    with open(file_path, "r") as f:
        geojson_data = json.load(f)
    
    # If it's a FeatureCollection, extract the first feature
    if geojson_data["type"] == "FeatureCollection":
        feature = geojson_data["features"][0]  # Use the first feature
    elif geojson_data["type"] == "Feature":
        feature = geojson_data  # It's already a single feature
    else:
        raise ValueError("Unsupported GeoJSON structure: 'Feature' or 'FeatureCollection' expected.")
    
    # Check for 'geometry' key
    if "geometry" not in feature:
        raise KeyError("The GeoJSON feature does not contain a 'geometry' key.")
    
    return feature




def get_image_sample_coordinates(image_path: str, 
                                 sample_size: int = 512, 
                                 num_samples: int = 10, 
                                 region_geojson: Optional[str] = None) -> gpd.GeoDataFrame:
    """
    Get random sample coordinates within a GeoJSON polygon from an orthophoto.
    These coordinates will be used to find sample regions of the larger orthophoto.
    If no region boundary GeoJSON file name is passed, we will use image boundaries.

    Parameters:
        image_path (str): Path to the orthophoto image.
        sample_size (int): Size of the square samples (e.g., 512 for 512x512).
        num_samples (int): Number of random samples to extract.
        region_geojson (str): GeoJSON polygon defining the region of interest.

    Returns:
        gpd.GeoDataFrame: GeoDataFrame containing sample bounding boxes.
    """
    region_polygon = None

    # Samples must be within region, if provided
    if region_geojson:
        try:
            # Get region contour polygon from GeoJSON file
            region_contour = load_geojson(region_geojson)
            region_polygon = shape(region_contour["geometry"])
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error loading GeoJSON: {e}")
            print("Proceeding without region constraints.")

    if region_polygon:
        print("Region polygon successfully loaded. Restricting samples to the polygon.")
    else:
        print("No valid region polygon. Sampling from the entire image.")
    

    with rasterio.open(image_path) as src:
        # Read the raster's transform and bounds
        transform = src.transform
        width, height = src.width, src.height

        # Collect valid samples
        samples = []
        attempts = 0
        max_attempts = num_samples * 10  # Limit to avoid infinite loops
        
        while len(samples) < num_samples and attempts < max_attempts:
            # Generate a random top-left corner in pixel coordinates
            x = random.randint(0, width - sample_size)
            y = random.randint(0, height - sample_size)

            # Convert top-left corner to geographic coordinates
            top_left_lon, top_left_lat = rasterio.transform.xy(transform, y, x, offset="ul")
            bottom_right_lon, bottom_right_lat = rasterio.transform.xy(
                transform, y + sample_size, x + sample_size, offset="lr"
            )

            # Setup correct GDF geometry for boxes
            sample_box = box(top_left_lon, bottom_right_lat, bottom_right_lon, top_left_lat)

            # Check if the sample box is fully within the polygon (if available)
            if not region_polygon or (region_polygon and region_polygon.contains(sample_box)):
                samples.append(sample_box)

            attempts += 1

        if attempts >= max_attempts:
            print(f"Warning: Only {len(samples)} samples generated within the polygon after {max_attempts} attempts.")

     # Create a GeoDataFrame with the samples
    samples_gdf = gpd.GeoDataFrame(geometry=samples, crs=src.crs.to_string())
    return samples_gdf


def get_samples_from_gdf(gdf, image_path):
    """
    Extract raster samples based on the polygons in a GeoDataFrame.

    Parameters:
        gdf (gpd.GeoDataFrame): GeoDataFrame containing sample polygons.
        image_path (str): Path to the orthophoto image.

    Returns:
        List of numpy arrays representing the raster samples.
    """
    samples = []
    with rasterio.open(image_path) as src:
        for geom in gdf.geometry:
            minx, miny, maxx, maxy = geom.bounds # Get the bounding box of the geometry
            
            # Convert bounding box to pixel coordinates
            window = rasterio.windows.from_bounds(minx, miny, maxx, maxy, transform=src.transform)
            sample = src.read(window=window)
            sample = np.moveaxis(sample, 0, -1)  # Move channel axis for display (else dims wrong for plt)
            samples.append(sample)
    return samples


def plot_samples(samples):
    """
    Plot a list of image samples for visualization.
    
    Parameters:
        samples (list): List of numpy arrays representing image samples.
    """
    num_samples = len(samples)
    cols = 4
    rows = (num_samples // cols) + (num_samples % cols > 0)
    
    plt.figure(figsize=(15, rows * 4))
    for i, sample in enumerate(samples):
        plt.subplot(rows, cols, i + 1)
        plt.imshow(sample, cmap='Greens')  # Move channel axis for display
        plt.axis('off')
    plt.tight_layout()
    plt.show()
