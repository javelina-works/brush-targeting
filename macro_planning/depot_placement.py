from typing import Union
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
from pulp import LpProblem, LpVariable, lpSum, LpMinimize, PULP_CBC_CMD, HiGHS_CMD
import matplotlib.pyplot as plt


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
    depots_gdf = gpd.GeoDataFrame(selected_depots, crs=cell_gdf.crs)

    return depots_gdf



def assign_cells_to_depot(depots_gdf, cell_gdf):

    def distance_to_depot(polygon, depot):
        return polygon.centroid.distance(Point(depot.x, depot.y))

    # Determine the closest depot for multi-depot cells
    def closest_depot(polygon, depot_IDs):
        distances = {i: distance_to_depot(polygon, depots_gdf.loc[depots_gdf['depot_id'] == i]['geometry']) for i in depot_IDs}
        return min(distances, key=distances.get)


    # Assign each cell to its covering depots
    cell_gdf['associated_depots'] = cell_gdf['geometry'].apply(
        lambda polygon: [
            depot.get("depot_id", i) for i, depot in depots_gdf.iterrows()
            if polygon.within(depot['geometry'].buffer(depot.get("depot_radius", 0)))
        ]
    )

    cell_gdf['closest_depot'] = cell_gdf.apply(
        lambda row:
            row['associated_depots'][0]
            if len(row['associated_depots']) == 1
            else closest_depot(row['geometry'], row['associated_depots']),
            axis=1
    )


    # Find minimum enclosing circle of region from depot
    dict_of_regions = {k:group for k, group in cell_gdf.groupby('closest_depot')}
    min_enclosing_radii = [] # Add min_enclosing_rad to depots_gdf

    for i, depot in depots_gdf.iterrows():
        depot_ID = depot.get("depot_id", i)
        region_cells = dict_of_regions[depot_ID] # Cells closest to our depot

        if region_cells is not None:
           center, radius = minimum_enclosing_circle(region_cells)
        else:
            radius = 0

        min_enclosing_radii.append(radius)

    # Final update to depots_gdf  
    depots_gdf['min_enclosing_rad'] = min_enclosing_radii

    return depots_gdf, cell_gdf


from scipy.spatial import ConvexHull
from shapely.geometry import Polygon
from shapely.ops import unary_union


def minimum_enclosing_circle(cell_gdf: gpd.GeoDataFrame) -> tuple:
    """
    Compute the minimum enclosing circle for the convex hull of a given GeoDataFrame of cells.

    Parameters:
        cell_gdf (GeoDataFrame): A GeoDataFrame containing cell geometries.

    Returns:
        tuple: (center_x, center_y, radius) of the minimum enclosing circle.
    """
    def dist(p1, p2):
        """Compute the Euclidean distance between two points."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def circle_from_three_points(p1, p2, p3):
        """Compute the circle defined by three points."""
        ax, ay = p1
        bx, by = p2
        cx, cy = p3
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
        uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
        center = (ux, uy)
        radius = dist(center, p1)
        return center, radius

    def welzl(points, boundary):
        """Recursive function for Welzl's algorithm."""
        if len(points) == 0 or len(boundary) == 3:
            if len(boundary) == 0:
                return (0, 0), 0
            elif len(boundary) == 1:
                return boundary[0], 0
            elif len(boundary) == 2:
                center = ((boundary[0][0] + boundary[1][0]) / 2, (boundary[0][1] + boundary[1][1]) / 2)
                radius = dist(boundary[0], boundary[1]) / 2
                return center, radius
            elif len(boundary) == 3:
                return circle_from_three_points(*boundary)

        point = points[-1]
        center, radius = welzl(points[:-1], boundary)

        if dist(center, point) <= radius:
            return center, radius

        return welzl(points[:-1], boundary + [point])

    # Compute the convex hull of the combined geometries in the GeoDataFrame
    convex_hull = cell_gdf.unary_union.convex_hull
    if not isinstance(convex_hull, Polygon):
        raise ValueError("Convex hull could not be computed as a valid polygon.")

    # Extract the points from the polygon's exterior
    points = list(convex_hull.exterior.coords)

    # Compute the convex hull of the points
    hull = ConvexHull(points)
    hull_points = [points[vertex] for vertex in hull.vertices]

    # Run Welzl's algorithm on the convex hull points
    center, radius = welzl(hull_points, [])
    return center, radius