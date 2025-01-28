import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import distance_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def calculate_intra_cell_workload(cell_targets):
    """
    Calculate the intra-cell workload as the sum of the Minimum Spanning Tree (MST) distances.

    Parameters:
    - cell_targets: ndarray of shape (n, 2)
        Coordinates of the targets within a cell.

    Returns:
    - mst_distance: float
        Total intra-cell workload based on MST distances.
    """
    if cell_targets.shape[0] < 2:
        return 0

    # Compute pairwise distance matrix
    pairwise_dist = distance_matrix(cell_targets, cell_targets)

    mst = minimum_spanning_tree(pairwise_dist) # Compute MST and sum its edges
    mst_distance = mst.sum()
    return mst_distance


def calculate_cell_workloads(cells_gdf, targets_gdf):
    """
    Determine workload per cell from targets. 
    Updates 'cells_gdf' in-place, adding columns.

    Parameters:
    - cells_gdf: GeoDataFrame
        GeoDataFrame of cells (e.g., Voronoi or other tessellation).
    - targets_gdf: GeoDataFrame
        GeoDataFrame of target centroids.
    """
    # Assure GDFs are valid
    cells_gdf["geometry"] = cells_gdf["geometry"].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)
    targets_gdf["geometry"] = targets_gdf["geometry"].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)

    updated_cells_gdf = cells_gdf.copy()
    updated_targets_gdf = targets_gdf.copy()

    # 1. Associate targets with cells
    joined_gdf = gpd.sjoin(updated_targets_gdf, updated_cells_gdf, how="left", predicate="intersects")
    joined_gdf = joined_gdf[joined_gdf["index_right"].notna()]
    updated_targets_gdf["parent_cell_id"] = joined_gdf["index_right"]  # Assign cell_id based on spatial join

    # Drop targets without a parent_cell_id
    updated_targets_gdf = updated_targets_gdf[updated_targets_gdf["parent_cell_id"].notna()].copy()
    
    # 2. Determine total work in each cell
    counts = updated_targets_gdf.groupby('parent_cell_id').size()  # Count centroids in each cell
    updated_cells_gdf["target_count"] = updated_cells_gdf.index.map(counts).fillna(0).astype(int)  # Fill NaN with 0

     # 2. Calculate workloads for each cell
    workloads = []
    for cell_id, cell_row in updated_cells_gdf.iterrows():
        # Get targets associated with the current cell
        cell_targets = updated_targets_gdf[updated_targets_gdf["parent_cell_id"] == cell_id]

        if not cell_targets.empty:
            # Extract target coordinates
            target_coords = np.array([(point.x, point.y) for point in cell_targets["geometry"]])
            workload = calculate_intra_cell_workload(target_coords)
        else:
            workload = 0  # No targets in the cell

        workloads.append(workload)

    updated_cells_gdf["intra_workload"] = workloads # Add workload as a new column in cells_gdf

    return updated_cells_gdf, updated_targets_gdf


def targets_to_depots(cell_gdf, targets_gdf):
    """
    Adds a column to targets_gdf indicating the closest depot based on the parent cell.

    Parameters:
    - cell_gdf: GeoDataFrame
        GeoDataFrame of cells with 'geometry' and 'depot' columns.
    - targets_gdf: GeoDataFrame
        GeoDataFrame of targets with 'geometry' and 'parent_cell_id' columns.

    Returns:
    - GeoDataFrame: Updated targets_gdf with a 'closest_depot' column.
    """
    # Ensure necessary columns are present
    if "parent_cell_id" not in targets_gdf.columns or "closest_depot" not in cell_gdf.columns:
        raise ValueError("Missing required columns: 'parent_cell_id' in targets_gdf or 'closest_depot' in cell_gdf")

    # Initialize the closest_depot column
    targets_gdf["closest_depot"] = None

    # Iterate over each target
    for idx, target in targets_gdf.iterrows():
        parent_cell_id = target["parent_cell_id"] # Get the parent cell ID
        # if gpd.isna(parent_cell_id):
        #     continue # If no parent cell, skip this target

        parent_cell = cell_gdf.loc[parent_cell_id] # Get the parent cell row
        targets_gdf.at[idx, "closest_depot"] = parent_cell["closest_depot"] # Assign the depot as the closest depot

    return targets_gdf


# Useful visualizations
# ========================

def plot_cells_with_targets(cells_gdf):
    """
    Plot the region with cells colored by the number of target centroids.

    Parameters:
    - cells_gdf: GeoDataFrame
        GeoDataFrame of cells (e.g., Voronoi or other tessellation).
    - targets_gdf: GeoDataFrame
        GeoDataFrame of target centroids.
    """
    # Plot cells colored by the count of centroids
    fig, ax = plt.subplots(figsize=(10, 8))
    cells_gdf.plot(
        column="target_count",
        cmap="viridis",
        legend=True,
        edgecolor="black",
        ax=ax
    )

    # Annotate cells with the number of centroids
    for _, row in cells_gdf.iterrows():
        if row["target_count"]:  # Only label cells with centroids
            ax.annotate(
                text=row["target_count"],
                xy=row["geometry"].centroid.coords[0],
                ha="center",
                va="center",
                fontsize=8,
                color="white"
            )

    plt.title("Cells Colored by Number of Target Centroids")
    plt.show()


def plot_cells_ids(cells_gdf):
    """
    Plot the region with cells (labeled with IDs) colored by the number of target centroids.

    Parameters:
    - cells_gdf: GeoDataFrame
        GeoDataFrame of cells (e.g., Voronoi or other tessellation).
    - targets_gdf: GeoDataFrame
        GeoDataFrame of target centroids.
    """
    # Plot cells colored by the count of centroids
    fig, ax = plt.subplots(figsize=(10, 8))
    cells_gdf.plot(
        column="target_count",
        cmap="viridis",
        legend=True,
        edgecolor="black",
        ax=ax
    )

    # Annotate cells with the number of centroids
    for _, row in cells_gdf.iterrows():
        ax.annotate(
            text=row["cell_id"],
            xy=row["geometry"].centroid.coords[0],
            ha="center",
            va="center",
            fontsize=8,
            color="white"
        )

    plt.title("Cells Colored by Number of Target Centroids")
    plt.show()