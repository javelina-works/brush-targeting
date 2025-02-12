import geopandas as gpd
import json
from shapely.geometry import Polygon, MultiPoint, Point
import numpy as np
from shapely.ops import voronoi_diagram
from typing import Optional

from backend.graphql.utils import fetch_map_asset, save_geojson_file
from backend.graphql.types import MapAsset, GeoJSONInput
from backend.config import DISPLAY_CRS, PROCESSING_CRS, REGION_FILE, VORONOI_FILE

def generate_region_tesselation(
    location_id: str,
    job_id: str,
    target_area_acres: float = 0.5, # Default to half an acre
    max_iterations: int = 15, # Default to 15 cycles
    geojson_file: Optional[GeoJSONInput] = None
) -> MapAsset:
    """
    Runs tessellation for the given location/job or uses an override GeoJSON.
    Returns the result as a GeoJSON dictionary.
    """

    # 1. Use client-provided GeoJSON, or fetch from storage
    if geojson_file is None :
        region_geojson = fetch_map_asset(location_id, job_id, REGION_FILE)
    else:
        try:
            region_name = geojson_file.name
            region_geojson = json.loads(geojson_file.geojson) # Load string to JSON
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid GeoJSON input: {e}")

    if region_geojson is None:
            raise ValueError(f"Missing region outline for location {location_id}, job {job_id}.")

    # 2. Convert JSON to GeoDataFrame
    region_gdf = gpd.GeoDataFrame.from_features(region_geojson["features"])
    region_gdf.set_crs(DISPLAY_CRS, inplace=True)

    # 3. Convert to projected CRS for area calculations
    region_gdf = region_gdf.to_crs(PROCESSING_CRS)
    target_area_sqm = target_area_acres * 4046.86

    # 4. Compute number of cells
    region_polygon = region_gdf.geometry.iloc[0]
    num_cells = int(region_polygon.area / target_area_sqm)

    # 5. Perform tessellation
    tessellated_gdf = centroidal_voronoi_tessellation(region_polygon, num_cells, max_iterations)
    tessellated_gdf = tessellated_gdf.to_crs(DISPLAY_CRS)
    tesselation_json = tessellated_gdf.to_json() # Save as json-formatted string

    # 6. Save generated tesselation
    filename = VORONOI_FILE
    if filename.endswith(".geojson"):  # Only load GeoJSON files
            filename = filename.replace(".geojson", "")  # Strip file extension

    success = save_geojson_file(location_id, job_id, filename, tesselation_json)
    if not success:
            raise ValueError(f"Unable to save generated tesselation output")

    # 6. Convert to GeoJSON and return
    return MapAsset(
        id=filename, 
        name=filename, 
        type="GeoJSON",
        geojson=tesselation_json
    )



def centroidal_voronoi_tessellation(region_polygon, num_points,
                                    max_iterations=10, tolerance=1e-3, region_crs="EPSG:32613"):
    """
    Perform Centroidal Voronoi Tessellation (CVT) to refine seed points for uniform partitions.
    
    Parameters:
        region_polygon (Polygon): The region to partition.
        num_points (int): Number of seed points.
        max_iterations (int): Maximum number of iterations for CVT.
        tolerance (float): Convergence threshold for point adjustments.
    
    Returns:
        GeoDataFrame: Voronoi polygons, centroids as GeoDataFrame.
    """
    # Step 1: Generate initial random points
    minx, miny, maxx, maxy = region_polygon.bounds
    points = []
    while len(points) < num_points:
        x, y = np.random.uniform(minx, maxx), np.random.uniform(miny, maxy)
        if region_polygon.contains(Point(x, y)):
            points.append(Point(x, y))

    # Step 2: Iteratively refine points
    for iteration in range(max_iterations):
        # Create Voronoi diagram
        multipoint = MultiPoint(points)
        voronoi_result = voronoi_diagram(multipoint, envelope=region_polygon, edges=False)

        # Check if Voronoi diagram has valid geometries
        if not voronoi_result.geoms:
            raise ValueError("Voronoi tessellation did not produce any valid polygons.")

        # Compute centroids of Voronoi polygons
        new_points = []
        for poly in voronoi_result.geoms:
            clipped_poly = poly.intersection(region_polygon)
            if clipped_poly.is_valid and not clipped_poly.is_empty:
                new_points.append(clipped_poly.centroid)
        
        # Stop if no valid centroids were found
        if not new_points:
            print("Warning: No valid centroids found in Voronoi tessellation. Stopping iterations.")
            break

        # Check for convergence (small adjustments)
        max_shift = max(point.distance(new_point) for point, new_point in zip(points, new_points))
        points = new_points  # Update points for next iteration

        if max_shift < tolerance:
            print(f"Converged after {iteration+1} iterations.")
            break
    else:
        print("Reached maximum iterations without full convergence.")

    # Create Voronoi polygons GeoDataFrame
    clipped_polygons = [poly.intersection(region_polygon) for poly in voronoi_result.geoms]
    voronoi_cells_gdf = gpd.GeoDataFrame({"geometry": clipped_polygons}, crs=region_crs)
    # voronoi_cells_gdf['cell_centroid'] = gpd.GeoSeries(points) # Add centroids as column
    voronoi_cells_gdf['cell_id'] = range(len(voronoi_cells_gdf)) # Add an 'id' column to the Voronoi cells GeoDataFrame

    return voronoi_cells_gdf
