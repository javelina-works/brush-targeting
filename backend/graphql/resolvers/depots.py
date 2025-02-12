import geopandas as gpd
import numpy as np
import json
from shapely.geometry import Point, Polygon
from pulp import LpProblem, LpVariable, lpSum, LpMinimize, PULP_CBC_CMD, HiGHS_CMD
from typing import Optional, Union

from backend.graphql.utils import fetch_map_asset, save_geojson_file
from backend.graphql.types import MapAsset
from backend.config import DISPLAY_CRS, PROCESSING_CRS, REGION_FILE, VORONOI_FILE, DEPOT_FILE

def generate_depots(
    location_id: str,
    job_id: str,
    depot_radius: float = 225,  # Default 225 meters
    grid_density: int = 4       # Default 4 candidate points per cell
) -> MapAsset:
    """
    Runs depot placement based on the region outline and tessellated cells.
    Returns depot locations as a GeoJSON dictionary.
    """

    # 1. Fetch necessary assets (Region outline & Voronoi cells)
    region_geojson = fetch_map_asset(location_id, job_id, REGION_FILE)
    cells_geojson = fetch_map_asset(location_id, job_id, VORONOI_FILE)

    if region_geojson is None or cells_geojson is None:
        raise ValueError(f"Missing required assets for depot placement at location {location_id}, job {job_id}.")

    # 2. Convert JSON to GeoDataFrame
    region_gdf = gpd.GeoDataFrame.from_features(region_geojson["features"])
    region_gdf.set_crs(DISPLAY_CRS, inplace=True)

    cells_gdf = gpd.GeoDataFrame.from_features(cells_geojson["features"])
    cells_gdf.set_crs(DISPLAY_CRS, inplace=True)

    # 3. Convert to projected CRS for processing
    region_gdf = region_gdf.to_crs(PROCESSING_CRS)
    cells_gdf = cells_gdf.to_crs(PROCESSING_CRS)

    # 4. Compute depot locations
    depots_gdf = find_depots(depot_radius, cells_gdf, region_gdf, grid_density)

    # 5. Convert results back to WGS84 for mapping
    depots_gdf = depots_gdf.to_crs(DISPLAY_CRS)

    # 6. Convert to GeoJSON string
    depots_json = depots_gdf.to_json()

    # 7. Save generated depots
    filename = DEPOT_FILE
    if filename.endswith(".geojson"):  # Only load GeoJSON files
        filename = filename.replace(".geojson", "")  # Strip file extension

    success = save_geojson_file(location_id, job_id, filename, depots_json)
    if not success:
        raise ValueError(f"Unable to save generated depot output")

    # 8. Return response as a MapAsset
    return MapAsset(
        id=filename,
        name=filename,
        type="GeoJSON",
        geojson=depots_json
    )


def find_depots(depot_radius: float, cell_gdf: gpd.GeoDataFrame, region_polygon: Union[Polygon, gpd.GeoDataFrame], grid_density:int=2) -> gpd.GeoDataFrame:
    """
    Find the optimal depot locations to cover all cells within a given region.

    Parameters:
    - depot_radius (float): The radius within which a depot can cover a cell.
    - cell_gdf (GeoDataFrame): GeoDataFrame of cells with geometries (polygons).
    - region_polygon (Union[Polygon, GeoDataFrame]): The overall work region as a Polygon or GeoDataFrame.
    - grid_density (int): Density of points for candidate depot locations (higher is slower, more robust)

    Returns:
    - GeoDataFrame: GeoDataFrame containing the optimal depot locations.
    """
    # Validate inputs
    if depot_radius <= 0:
        raise ValueError("Depot radius must be a positive value.")
    if cell_gdf.empty:
        raise ValueError("The cells GeoDataFrame is empty.")
    if not isinstance(region_polygon, (Polygon, gpd.GeoDataFrame)):
        raise TypeError("Region polygon must be a Shapely Polygon or a GeoDataFrame.")
    
    if isinstance(region_polygon, gpd.GeoDataFrame):
        region_polygon = region_polygon.unary_union  # Combine geometries if a GeoDataFrame

    
    # Define bounds of the work region
    min_x, min_y, max_x, max_y = cell_gdf.total_bounds

    # Generate grid points with a fixed spacing
    grid_spacing = depot_radius / grid_density  # Adjust this value for finer or coarser grids (more candidate points)
    grid_points = [
        Point(x, y)
        for x in np.arange(min_x, max_x, grid_spacing)
        for y in np.arange(min_y, max_y, grid_spacing)
        if region_polygon.contains(Point(x, y))  # Only keep points within the work region
    ]

    # List of all points we will check for a possible valid depot location
    potential_depots = [polygon.centroid for polygon in cell_gdf['geometry']] + grid_points

    coverage_matrix = [] # Coverage matrix: is a given cell covered by a depot location?
    for polygon in cell_gdf['geometry']:
        row = [polygon.within(depot.buffer(depot_radius)) for depot in potential_depots]
        coverage_matrix.append(row)

    problem = LpProblem("Geometric_Set_Cover", LpMinimize) # ILP Problem Definition

    # Variables: 1 if depot is selected, 0 otherwise
    depot_vars = [LpVariable(f"depot_{i}", cat="Binary") for i in range(len(potential_depots))]
    problem += lpSum(depot_vars) # Objective: Minimize the number of depots

    # Constraints: Each polygon must be covered by at least one depot
    for i, polygon in enumerate(cell_gdf['geometry']):
        problem += lpSum(depot_vars[j] for j, covers in enumerate(coverage_matrix[i]) if covers) >= 1
    problem.solve(PULP_CBC_CMD(msg=False))

    # Extract selected depots
    selected_depots = [
        {"geometry": potential_depots[i], "depot_radius": depot_radius, "depot_id": f"depot_{i}"}
        for i, var in enumerate(depot_vars) if var.varValue == 1
    ]
    print(selected_depots)
    depots_gdf = gpd.GeoDataFrame(selected_depots, crs=cell_gdf.crs)

    return depots_gdf
