from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from shapely.geometry import LineString, Point
import geopandas as gpd
import pandas as pd

def calculate_tsp_route(route_targets_gdf, depot_point):
    """
    Calculate the TSP approximate shortest path for targets in a given route.

    Parameters:
    - route_targets_gdf: GeoDataFrame
        GeoDataFrame of targets for a specific route_id.
    - depot_point: shapely.geometry.Point
        Coordinates of the depot, used as the starting and ending point.

    Returns:
    - ordered_points: list of shapely.geometry.Point
        The ordered sequence of points representing the TSP route.
    - total_distance: float
        The total distance of the TSP route.
    """
    # Combine depot and targets into a single list of points
    points = [depot_point] + list(route_targets_gdf["geometry"])
    num_points = len(points)
    
    # Create distance matrix
    def distance_matrix():
        return [
            [points[i].distance(points[j]) for j in range(num_points)]
            for i in range(num_points)
        ]
    
    dist_matrix = distance_matrix()

    # Create the TSP solver
    manager = pywrapcp.RoutingIndexManager(len(dist_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(dist_matrix[from_node][to_node] * 1000)  # Scale for integer optimization

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Solve TSP
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        raise ValueError("No solution found for TSP!")

    # Extract the ordered sequence of points
    index = routing.Start(0)
    ordered_points = []
    while not routing.IsEnd(index):
        node_index = manager.IndexToNode(index)
        ordered_points.append(points[node_index])
        index = solution.Value(routing.NextVar(index))
    ordered_points.append(points[0])  # Return to depot

    # Calculate total distance
    total_distance = sum(
        ordered_points[i].distance(ordered_points[i + 1]) for i in range(len(ordered_points) - 1)
    )
    
    return ordered_points, total_distance



def calculate_all_routes_tsp(routed_targets_gdf, depot_point, depot_id):
    """
    Calculate the TSP route for all targets grouped by route_id for a specific depot.

    Parameters:
    ----------
    routed_targets_gdf : GeoDataFrame
        GeoDataFrame of targets with route_id and geometry columns.

    depot_point : shapely.geometry.Point
        The coordinates of the depot.

    depot_id : object
        The identifier of the depot (used for filtering and labeling).

    Returns:
    -------
    results : dict
        Dictionary where keys are route_ids and values are:
        {'ordered_points': list of shapely.geometry.Point, 'total_distance': float}.
    """
    results = {}
    unique_route_ids = routed_targets_gdf["route_id"].unique()

    # Filter targets associated with the given depot
    route_targets_gdf = routed_targets_gdf[routed_targets_gdf['closest_depot'] == depot_id]

    for route_id in unique_route_ids:
        route_targets = route_targets_gdf[route_targets_gdf["route_id"] == route_id]
        if not route_targets.empty:
            ordered_points, total_distance = calculate_tsp_route(route_targets, depot_point)
            results[route_id] = {"ordered_points": ordered_points, "total_distance": total_distance}

    return results




def create_micro_routes_gdf(results, macro_routes_gdf, depot_point, depot_id):
    """
    Create a GeoDataFrame of polylines for the solved micro routes.

    Parameters:
    - results: dict
        Dictionary of TSP results, where keys are route_ids and values are
        {'ordered_points': list of shapely.geometry.Point, 'total_distance': float}.
    - macro_routes_gdf: GeoDataFrame
        GeoDataFrame containing route information (e.g., route_cells, route_id).
    - depot_point: shapely.geometry.Point
        Coordinates of the depot.

    Returns:
    - routes_gdf: GeoDataFrame
        GeoDataFrame of polylines with columns for 'route_id', 'closest_depot', and 'route_cells'.
    """
    route_ids = []
    polylines = []
    closest_depots = []
    closest_depots_point = []
    route_cells_list = []

    for route_id, data in results.items():
        ordered_points = data['ordered_points']
        route_line = LineString(ordered_points)  # Create a LineString from the ordered points

        # Get the corresponding row in macro_routes_gdf for additional attributes
        macro_route_row = macro_routes_gdf[macro_routes_gdf['route_id'] == route_id].iloc[0]
        # route_cells = macro_route_row['route_cells']

        # Convert from np int64 to regular int
        route_cells = [int(cell) for cell in macro_route_row['route_cells']]

        # Append data for the GeoDataFrame
        route_ids.append(route_id)
        polylines.append(route_line)
        closest_depots.append(depot_id)
        closest_depots_point.append(depot_point)
        route_cells_list.append(route_cells)

    # Create the GeoDataFrame
    routes_gdf = gpd.GeoDataFrame({
        "route_id": route_ids,
        "geometry": polylines,
        "closest_depot": closest_depots,
        "route_cells": route_cells_list
    }, crs=macro_routes_gdf.crs)
    
    return routes_gdf



def create_all_micro_routes_gdf(routed_targets_gdf, macro_routes_gdf, depots_gdf):
    """
    Create a GeoDataFrame of micro routes for all depot points.

    Parameters:
    ----------
    routed_targets_gdf : GeoDataFrame
        GeoDataFrame of all targets, including columns:
        - 'route_id': The route ID for each target.
        - 'closest_depot': The depot associated with the target.
        - 'geometry': The geometry of each target point.

    macro_routes_gdf : GeoDataFrame
        GeoDataFrame of macro routes, including:
        - 'route_id': Unique route identifier.
        - 'route_depot': Depot associated with the route.
        - 'route_cells': List of cells included in the route.
        - 'geometry': The geometry of the macro route.

    depots_gdf : GeoDataFrame
        GeoDataFrame of depots, including:
        - 'depot_id': Unique depot identifier.
        - 'geometry': Point geometry of the depot.

    Returns:
    -------
    all_routes_gdf : GeoDataFrame
        GeoDataFrame of all micro routes, including:
        - 'route_id': Unique route identifier.
        - 'geometry': LineString geometry of the TSP route.
        - 'closest_depot': The depot associated with the route.
        - 'route_cells': List of cells covered by the route.
    """
    all_routes = []

    # Iterate over each depot
    for _, depot_row in depots_gdf.iterrows():
        depot_id = depot_row['depot_id']
        depot_point = depot_row['geometry']

        # Filter targets for the current depot
        depot_targets_gdf = routed_targets_gdf[routed_targets_gdf['closest_depot'] == depot_id]

        if depot_targets_gdf.empty:
            continue

        # Solve TSP for all routes associated with this depot
        tsp_results = calculate_all_routes_tsp(depot_targets_gdf, depot_point, depot_id)

        # Create micro routes GeoDataFrame for this depot
        depot_routes_gdf = create_micro_routes_gdf(tsp_results, macro_routes_gdf, depot_point, depot_id)

        all_routes.append(depot_routes_gdf)

    # Combine all depot routes into a single GeoDataFrame
    all_routes_gdf = gpd.GeoDataFrame(pd.concat(all_routes, ignore_index=True), crs=macro_routes_gdf.crs)

    return all_routes_gdf