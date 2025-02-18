import geopandas as gpd
import pandas as pd
import numpy as np

# TODO: remove plant_search dependency
from backend.macro_planning.macro_utils import calculate_intra_cell_workload


def create_cells_depots_df(depots_gdf, cells_gdf, target_crs="EPSG:32613"):
    """
    Associates cells with depots, computing the closest depot and associated depots.
    Ensures CRS is in meters for accurate distance calculations.
    
    Parameters:
        depots_gdf (GeoDataFrame): Depots with geometry and radius.
        cells_gdf (GeoDataFrame): Cells with geometry.
        target_crs (str): Target CRS (e.g., "EPSG:32614") for distance calculations.
    
    Returns:
        cells_depots_df: DataFrame containing cell-depot associations with distances.
    """

    # Copy and reproject GeoDataFrames to the target CRS
    depots_proj = depots_gdf.to_crs(target_crs)
    cells_proj = cells_gdf.to_crs(target_crs)

    records = [] # Initialize list to store results

    # Iterate through each cell to compute associations
    for _, cell in cells_proj.iterrows():

        # Filter depots where the cell is fully within the depot's range radius
        associated_depots = [
            depot["depot_id"]
            for _, depot in depots_proj.iterrows()
            if cell.geometry.within(depot["geometry"].buffer(depot.get("depot_radius", 0)))
        ]
        
        # Compute distances to associated depots and find the closest one
        if associated_depots:
            distances = {
                depot["depot_id"]: cell.geometry.centroid.distance(depot["geometry"])
                for _, depot in depots_proj[depots_proj["depot_id"].isin(associated_depots)].iterrows()
            }
            closest_depot = min(distances, key=distances.get)
            closest_distance = distances[closest_depot]
        else:
            closest_depot = None
            closest_distance = None

        records.append({
            "cell_id": cell["cell_id"],
            "closest_depot": closest_depot,
            "associated_depots": associated_depots,
            "distance": closest_distance,
        })

    cells_depots_df = pd.DataFrame(records)
    return cells_depots_df



def create_cell_targets_df(cells_gdf, targets_gdf):
    """
    Associates each target with a cell

    Parameters:
    - targets_gdf: GeoDataFrame
        GeoDataFrame of target centroids.
    - cells_gdf: GeoDataFrame
        GeoDataFrame of cells (e.g., Voronoi or other tessellation).
    """
    # Assure GDFs are valid
    targets_gdf["geometry"] = targets_gdf["geometry"].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)
    cells_gdf["geometry"] = cells_gdf["geometry"].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)

    # Targets within each cell
    joined_gdf = gpd.sjoin(targets_gdf, cells_gdf, how="left", predicate="intersects")
    
    # Remove all targets not in any cell (out of bounds)
    joined_gdf = joined_gdf[joined_gdf["index_right"].notna()]

    cell_targets_df = joined_gdf.assign(
        target_index=joined_gdf.index,
        target_id=joined_gdf["target_id"],
        cell_id=joined_gdf["index_right"]
    ).reset_index(drop=True)[["cell_id", "target_index", "target_id", "geometry"]]

    return cell_targets_df



def create_cell_workloads_df(cells_gdf, targets_gdf, cell_targets_df=None):
    """
    Creates a DataFrame summarizing the workload for each cell, including target count and intra-cell workload.

    Parameters:
    - cells_gdf (GeoDataFrame): GeoDataFrame containing cell geometries.
    - targets_gdf (GeoDataFrame): GeoDataFrame containing target geometries.
    - cell_targets_df (DataFrame, optional): Precomputed DataFrame associating targets with cells.

    Returns:
    - DataFrame: A DataFrame containing cell_id, target_count, and workload for each cell.
    """
    # Assure GDFs are valid
    cells_gdf["geometry"] = cells_gdf["geometry"].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)
    targets_gdf["geometry"] = targets_gdf["geometry"].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)

    # Create cell-target associations if not passed in
    if cell_targets_df is None:
        cell_targets_df = create_cell_targets_df(cells_gdf, targets_gdf)

    cell_workloads = []
    for cell_id, group in cell_targets_df.groupby("cell_id"):
        target_ids = group['target_id'].values # IDs of all targets associated with this cell_id

        # Get GDFs of all these targets
        cell_targets = targets_gdf[targets_gdf['target_id'].isin(target_ids)]

        # Extract coordinates from geometry
        targets_coords = np.array([[geom.x, geom.y] for geom in cell_targets["geometry"]])

        workload = calculate_intra_cell_workload(targets_coords) if len(targets_coords) > 1 else 0
        cell_workloads.append({
            "cell_id": cell_id,
            "target_count": len(group),
            "workload": workload
        })

    cell_workloads_df = pd.DataFrame(cell_workloads)
    return cell_workloads_df



def create_targets_routes_gdf(targets_gdf, cells_gdf, macro_routes_gdf, cell_targets_df=None):
    """
    Create a GeoDataFrame that links each target with its corresponding route and depot information.

    Parameters:
    ----------
    targets_gdf : GeoDataFrame
        A GeoDataFrame containing the target points. Should include the geometry of the targets.

    cells_gdf : GeoDataFrame
        A GeoDataFrame containing spatial partitioning of the region into cells.

    macro_routes_gdf : GeoDataFrame
        A GeoDataFrame containing macro routes with the following required columns:
        - `route_id` (object): Unique identifier for each route.
        - `route_depot` (object): Identifier for the depot associated with the route.
        - `route_cells` (object): A list or iterable containing the `cell_id` values included in the route.

    cell_targets_df : GeoDataFrame, optional
        A GeoDataFrame associating targets (`targets_gdf`) with their respective cells (`cells_gdf`).
        If not provided, the function will generate it using `create_cell_targets_df(cells_gdf, targets_gdf)`.

    Returns:
    -------
    targets_routes_gdf : GeoDataFrame
        A GeoDataFrame that is a copy of `cell_targets_df`, with the following additional columns:
        - `route_id` (object): The ID of the route associated with the target.
        - `closest_depot` (object): The depot associated with the route containing the target.

    Functionality:
    -------------
    1. If `cell_targets_df` is not provided, it generates this DataFrame using the provided `cells_gdf` and `targets_gdf`.
    2. Creates a mapping from `cell_id` to `route_id` and `closest_depot` using the `macro_routes_gdf`.
    3. Updates `cell_targets_df` by mapping the route and depot information to each target based on its `cell_id`.
    4. Returns the updated GeoDataFrame (`targets_routes_gdf`) with added route and depot information.

    Example:
    --------
    >>> targets_routes_gdf = create_targets_routes_gdf(targets_gdf, cells_gdf, macro_routes_gdf)
    >>> print(targets_routes_gdf.head())

    | cell_id | target_index | target_id | geometry     | route_id | closest_depot |
    |---------|--------------|-----------|--------------|----------|---------------|
    | 1       | 0            | T001      | POINT(...)   | R001     | DepotA        |
    | 2       | 1            | T002      | POINT(...)   | R002     | DepotB        |

    Notes:
    ------
    - Assumes `macro_routes_gdf` has a `route_cells` column containing iterable lists of `cell_id` values.
    - Efficient for large datasets by leveraging dictionary mapping and vectorized operations.
    """

    if cell_targets_df is None:
        cell_targets_df = create_cell_targets_df(cells_gdf, targets_gdf)

    targets_routes_gdf = cell_targets_df.copy()

    # Create a mapping of cell_id to route_id and closest_depot
    cell_to_route = {}
    for _, route in macro_routes_gdf.iterrows():
        for cell_id in route.route_cells:
            cell_to_route[cell_id] = {
                'route_id': route.route_id,
                'closest_depot': route.route_depot
            }

    # Apply the mapping to the targets_routes_gdf
    def map_route_info(row):
        cell_id = row['cell_id']
        if cell_id in cell_to_route:
            return pd.Series(cell_to_route[cell_id])
        return pd.Series({'route_id': None, 'closest_depot': None})

    targets_routes_gdf[['route_id', 'closest_depot']] = targets_routes_gdf.apply(map_route_info, axis=1)

    return targets_routes_gdf


