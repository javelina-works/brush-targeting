import numpy as np
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def compute_tsp_path(centroids):
    """
    Compute the most efficient path connecting all centroids (Traveling Salesman Problem).

    Parameters:
        centroids (list of tuple): List of (x, y) coordinates representing region centroids.

    Returns:
        list of int: The indices of the centroids in the order of the most efficient path.
    """
    # Compute pairwise distances between centroids
    distance_matrix = cdist(centroids, centroids, metric='euclidean')

    # Use a simple nearest neighbor heuristic to approximate the solution
    n = len(centroids)
    visited = [False] * n
    path = []
    current_node = 0
    path.append(current_node)
    visited[current_node] = True

    for _ in range(n - 1):
        # Find the nearest unvisited neighbor
        next_node = np.argmin(
            [distance_matrix[current_node, j] if not visited[j] else np.inf for j in range(n)]
        )
        path.append(next_node)
        visited[next_node] = True
        current_node = next_node

    # Return to the starting point to complete the cycle
    path.append(path[0])  # Optional: If a closed loop is needed
    return path

def calculate_optimal_route(centroids):
    """
    Calculate the optimal route connecting all centroids using OR-Tools.

    Parameters:
        centroids (list of tuple): List of (x, y) coordinates.

    Returns:
        list of int: Optimal order of centroids.
    """
    # Compute the pairwise distance matrix
    distance_matrix = cdist(centroids, centroids, metric='euclidean')

    # Create the routing index manager
    num_locations = len(distance_matrix)
    manager = pywrapcp.RoutingIndexManager(num_locations, 1, 0)  # 1 vehicle, start at index 0

    # Create the routing model
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node])  # OR-Tools expects integer distances

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define the cost of each arc (distance between locations)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Set search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 10  # Limit to 10 seconds for optimization

    # Solve the problem
    solution = routing.Solve()

    # Extract the optimal path
    if solution:
        optimal_path = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            optimal_path.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        optimal_path.append(optimal_path[0])  # Return to start
        return optimal_path
    else:
        raise Exception("No solution found!")

def calculate_total_distance(centroids, path):
    """
    Calculate the total distance of a given path.

    Parameters:
        centroids (list of tuple): List of (x, y) coordinates.
        path (list of int): Order of centroids in the path.

    Returns:
        float: Total distance of the path.
    """
    total_distance = 0.0
    for i in range(len(path) - 1):
        total_distance += np.linalg.norm(np.array(centroids[path[i]]) - np.array(centroids[path[i+1]]))
    return total_distance


def plot_tsp_path_on_image(image, centroids, path, show_labels=True):
    """
    Overlay the TSP path on the original image.

    Parameters:
        image (np.ndarray): Original image (2D or 3D).
        centroids (list of tuple): List of (x, y) coordinates.
        path (list of int): Order of centroids in the TSP path.
        show_labels (bool): Whether to show centroid indices on the image.
    """
    plt.figure(figsize=(10, 10))
    plt.imshow(image, cmap='gray')  # Adjust colormap if the image is grayscale

    # Overlay the TSP path
    ordered_centroids = [centroids[i] for i in path]
    x, y = zip(*ordered_centroids)
    plt.plot(x, y, 'o-', color='red', label='TSP Path', markersize=8, linewidth=2)

    # Optionally label each centroid
    if show_labels:
        for i, (cx, cy) in enumerate(centroids):
            plt.text(cx, cy, str(i), fontsize=12, color='white', ha='center', va='center')

    plt.title("TSP Path Overlaid on Image")
    plt.axis("off")
    plt.legend()
    plt.show()
