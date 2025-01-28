
# These are just methods to visualize results from routing solutions

# ==================================================
# Visualize Routes
# ==================================================
import math 
import matplotlib.pyplot as plt
from shapely.geometry import LineString
import matplotlib.cm as cm
import geopandas as gpd

def plot_vrp_solution(cell_gdf, distance_matrix, region_polygon, base_station_gdf, routes, title="VRP Solution"):
    """
    Plots the VRP solution showing non-zero trips.

    Args:
        cell_gdf (GeoDataFrame): GeoDataFrame with polygon geometries.
        distance_matrix (np.ndarray): Distance matrix used in the VRP.
        region_polygon (shapely.geometry.Polygon): Polygon outlining the region.
        base_station_gdf (GeoDataFrame): GeoDataFrame containing the base station point.
        routes (list of lists): Routes for each vehicle.
        title (str): Title for the plot.
    """
    # Extract centroids
    centroids = cell_gdf.cell_centroid
    
    # Extract base station point
    base_station = base_station_gdf.geometry.iloc[0]  # Assuming single base station
    
    # Plot centroids, region outline, and base station
    fig, ax = plt.subplots(figsize=(12, 10))
    gpd.GeoDataFrame({"geometry": [region_polygon]}).boundary.plot(ax=ax, color="blue", linestyle="--", label="Simplified Region Outline")
    cell_gdf.boundary.plot(ax=ax, color="blue", linewidth=1, alpha=0.5, label="Voronoi Cells")  # Region cells
    base_station_gdf.plot(ax=ax, color='red', markersize=80, marker='*', zorder=10, label='Base Station')

    for i, centroid in enumerate(centroids):
        ax.scatter(centroid.x, centroid.y, color='blue', s=20, alpha=0.5, label='Centroid' if i == 0 else "")
        ax.text(centroid.x, centroid.y, str(i), fontsize=10, ha='right')
    
    # Generate a colormap for routes
    cmap = plt.get_cmap("tab20", len(routes))  # Tab10 provides distinct colors
    
    # Plot routes
    for route_idx, route in enumerate(routes):
        color = cmap(route_idx)  # Unique color for each route
        full_route = route + [route[0]]  # Ensure route returns to base station
        
        for i in range(len(full_route) - 1):
            from_node = full_route[i]
            to_node = full_route[i + 1]
            
            if from_node == len(centroids):  # From base station
                start_point = base_station
            else:
                start_point = centroids.iloc[from_node]
            
            if to_node == len(centroids):  # To base station
                end_point = base_station
            else:
                end_point = centroids.iloc[to_node]
            
            if distance_matrix[from_node][to_node] > 0:
                # Draw line between nodes
                line = LineString([start_point, end_point])
                ax.plot(*line.xy, color=color, linestyle='-', linewidth=2, label=f"Route {route_idx}" if i == 0 else "")
                
                # Annotate distance
                # midpoint = line.interpolate(0.5, normalized=True)
                # ax.text(midpoint.x, midpoint.y, f"{distance_matrix[from_node][to_node]:.0f}",
                #         fontsize=8, color='green')
    
    # Final plot details
    ax.set_title(title, fontsize=16)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc='upper right', fontsize=10)
    plt.grid(True)
    plt.show()



# Output route statistics for solved routes
def print_vehicle_details(routing, manager, solution, distance_dimension, max_distance):
    """
    Prints the objective value and each vehicle's cumulative distance, slack, and span.

    Args:
        routing (RoutingModel): OR-Tools RoutingModel instance.
        manager (RoutingIndexManager): OR-Tools RoutingIndexManager instance.
        solution (Assignment): Solution from the solver.
        distance_dimension (Dimension): Distance dimension object.
        max_distance (int): Upper bound for distance.
    """
    print("Objective Value:", solution.ObjectiveValue())
    print(f"Max allowed distance: {max_distance}")
    print("\nVehicle Details:")

    max_route_distance = 0
    min_route_distance = math.inf
    for vehicle_id in range(manager.GetNumberOfVehicles()):
        index = routing.Start(vehicle_id)
        route_distance = 0

        print(f"\nVehicle {vehicle_id}:")
        plan_output = f"\tRoute for vehicle {vehicle_id}:\n\t  "

        while not routing.IsEnd(index):
            plan_output += f" {manager.IndexToNode(index)} -> "
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )

        plan_output += f"{manager.IndexToNode(index)}"
        print(plan_output)

        # Cumulative distance for this vehicle
        end_index = routing.End(vehicle_id)
        cumulative_distance = solution.Value(distance_dimension.CumulVar(end_index))
        slack = max(0, max_distance - cumulative_distance)

        print(f"\tCumulative Distance: {cumulative_distance}") # Cumulative = Route Distance + Slack + Penalties
        print(f"\tSlack: {slack}")
        print(f"\tRoute Distance: {route_distance}") # sum of the direct transit costs (e.g., distances) between all nodes

        max_route_distance = max(route_distance, max_route_distance)
        min_route_distance = min(route_distance, min_route_distance) if route_distance>0 else min_route_distance

    print(f"Maximum of the route distances: {max_route_distance}m")
    print(f"Minimum of the route distances: {min_route_distance}m")


# ==================================================
# Visualize Distance Matrix
# ==================================================

import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString
import geopandas as gpd

def distance_matrix_heatmap(distance_matrix, title="Distance Matrix"):
    """
    Plots the distance matrix as a heatmap.

    Args:
        distance_matrix (np.ndarray): The 2D array of distances between nodes.
        title (str): Title for the plot.
    """
    plt.figure(figsize=(10, 8))
    plt.imshow(distance_matrix, cmap='viridis', interpolation='nearest')
    plt.colorbar(label='Distance')
    plt.title(title)
    plt.xlabel('Node Index')
    plt.ylabel('Node Index')
    plt.xticks(range(distance_matrix.shape[0]))
    plt.yticks(range(distance_matrix.shape[1]))
    plt.show()



def distance_matrix_plot_distances(cell_gdf, distance_matrix, region_polygon, base_station_gdf, title="Centroids and Routes"):
    """
    Plots centroids and draws lines with distances between each pair of centroids.

    Args:
        cell_gdf (GeoDataFrame): GeoDataFrame with a 'geometry' column containing centroids.
        distance_matrix (np.ndarray): 2D array of distances between centroids.
        title (str): Title for the plot.
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    gpd.GeoDataFrame({"geometry": [region_polygon]}).boundary.plot(ax=ax, color="blue", linestyle="--", label="Simplified Region Outline")
    cell_gdf.boundary.plot(ax=ax, color="blue", alpha=0.5, label="Voronoi Cells") # Region cells
    base_station_gdf.plot(ax=ax, color='red', markersize=60, marker='*', label='Base Station')
    

    # Plot centroids
    for i, centroid in enumerate(cell_gdf.cell_centroid):
        ax.scatter(centroid.x, centroid.y, color='blue', s=50, label='Centroid' if i == 0 else "")
        ax.text(centroid.x, centroid.y, str(i), fontsize=10, ha='right')
    
    # Draw lines and annotate distances from base station to centroids
    base_station = base_station_gdf.geometry.iloc[0]
    base_station_index = len(cell_gdf)

    for i, centroid in enumerate(cell_gdf.cell_centroid):
        # Create a line from base station to the centroid
        line = LineString([base_station, centroid])
        ax.plot(*line.xy, color='gray', linestyle='--', linewidth=1, alpha=0.35)
        
        # Annotate the distance on the line
        midpoint = line.interpolate(0.95, normalized=True)
        distance = distance_matrix[base_station_index, i]
        ax.text(midpoint.x, midpoint.y, f"{distance:.1f}", fontsize=8, color='red', alpha=0.8)

    # # WARNING: Turns into a cluster *immediately*
    # # Draw lines and annotate distances between all cells
    # for i, centroid_i in enumerate(cell_gdf.cell_centroid):
    #     for j, centroid_j in enumerate(cell_gdf.cell_centroid):
    #         if i < j:  # Avoid duplicate lines
    #             # Create a line between centroids
    #             line = LineString([centroid_i, centroid_j])
    #             ax.plot(*line.xy, color='gray', linestyle='--', linewidth=1, alpha=0.3)
                
    #             # Annotate the distance on the line
    #             midpoint = line.interpolate(0.5, normalized=True)
    #             distance = distance_matrix[i, j]
    #             ax.text(midpoint.x, midpoint.y, f"{distance:.1f}", fontsize=6, color='red')
    
    # Title and labels
    ax.set_title(title, fontsize=16)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc='upper right')
    plt.grid(True)
    plt.show()
