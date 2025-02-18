import geopandas as gpd

from backend.macro_planning.junctions import (
    create_cells_depots_df, create_cell_targets_df, create_cell_workloads_df
)
from backend.macro_planning.trip_routing import ( 
    solve_macro_routes, initialize_target_data
)
from backend.graphql.utils import fetch_map_asset, save_geojson_file
from backend.graphql.types import MapAsset
from backend.config import ( 
    DISPLAY_CRS, PROCESSING_CRS,
    APPROVED_TARGETS_FILE, VORONOI_FILE, DEPOT_FILE, MACRO_ROUTES_FILE
)

def solve_job_routes(location_id: str,
    job_id: str,
    t_num_vehicles: int = 25, 
    t_max_distance: int = 850,  # Max distance per trip (meters)
    t_distance_slack: int = 50,
    t_distance_slack_penalty: int = 10_000,
    t_slack_routes: int = 5
) -> MapAsset:

    # 1. Get GDFs
    cells_gdf, depots_gdf, targets_gdf = fetch_macro_route_gdfs(location_id, job_id)

    # 2. Initialize union GDFs
    cells_depots_df = create_cells_depots_df(depots_gdf, cells_gdf) # Find all depots able to serve each cell. Make note of closest "home" depot. 
    cell_targets_df = create_cell_targets_df(cells_gdf, targets_gdf) # Associate each cell with targets it contains
    cell_workloads_df  = create_cell_workloads_df(cells_gdf, targets_gdf, cell_targets_df) # Approximate total amount of work to be done in each cell

    # 3. Solve for macro routes
    target_data = initialize_target_data(t_num_vehicles, t_max_distance, t_distance_slack, 
                                     t_distance_slack_penalty, t_slack_routes)
    macro_routes_gdf = solve_macro_routes(cells_gdf, depots_gdf, targets_gdf, target_data)

    # 4. Convert to GeoJSON string
    macro_routes_gdf.to_crs(DISPLAY_CRS, inplace=True) #  Convert results back to WGS84 for mapping
    macro_routes_json = macro_routes_gdf.to_json()




    # 5. Save generated macro routes
    filename = MACRO_ROUTES_FILE
    if filename.endswith(".geojson"):  # Only load GeoJSON files
        filename = filename.replace(".geojson", "")  # Strip file extension

    success = save_geojson_file(location_id, job_id, filename, macro_routes_json)
    if not success:
        raise ValueError(f"Unable to save generated macro routes")

    # 6. Return response as a MapAsset
    return MapAsset(
        id=filename,
        name=filename,
        type="GeoJSON",
        geojson=macro_routes_json
    )


def fetch_macro_route_gdfs(location_id: str, job_id: str,):
    """
    Collect all GDFs needed to calculate our macro routes:
    - cells_gdf
    - depots_gdf
    - targets_gdf
    """
    # 1. Fetch necessary assets (Region outline & Voronoi cells)
    cells_geojson = fetch_map_asset(location_id, job_id, VORONOI_FILE)
    depots_geojson = fetch_map_asset(location_id, job_id, DEPOT_FILE)
    targets_geojson = fetch_map_asset(location_id, job_id, APPROVED_TARGETS_FILE)

    if depots_geojson is None or \
        cells_geojson is None or \
        targets_geojson is None:
        raise ValueError(f"Missing required assets for depot placement at location {location_id}, job {job_id}.")

    # 2. Convert JSON to GeoDataFrame
    cells_gdf = gpd.GeoDataFrame.from_features(cells_geojson["features"])
    cells_gdf.set_crs(DISPLAY_CRS, inplace=True)

    depots_gdf = gpd.GeoDataFrame.from_features(depots_geojson["features"])
    depots_gdf.set_crs(DISPLAY_CRS, inplace=True)

    targets_gdf = gpd.GeoDataFrame.from_features(targets_geojson["features"])
    targets_gdf.set_crs(DISPLAY_CRS, inplace=True)

    # 3. Convert to projected CRS for processing
    cells_gdf.to_crs(PROCESSING_CRS, inplace=True)
    depots_gdf.to_crs(PROCESSING_CRS, inplace=True)
    targets_gdf.to_crs(PROCESSING_CRS, inplace=True)

    return cells_gdf, depots_gdf, targets_gdf