import rasterio
import numpy as np
import cv2
from shapely.geometry import Polygon, MultiPoint, Point
from shapely.ops import voronoi_diagram
import geopandas as gpd


def extract_region_contour(geotiff_path):
    """
    Extract the contour of a binary mask using OpenCV's findContours.
    Then simplify polygon by reducing its vertices.

    Parameters:
        geotiff_path (str): Path to the GeoTIFF file.
        tolerance (float): Tolerance for simplification. Higher values result in greater simplification.

    Returns:
        GeoDataFrame: (Simplified) Contour as a polygon.
    """
    with rasterio.open(geotiff_path) as src:
        data = src.read(1) # Read the first band

        # Create a binary mask for valid data
        mask = (data != 0).astype(np.uint8)  # Convert to uint8 for OpenCV
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest_contour = max(contours, key=cv2.contourArea) # Assume largest contour is primary region

        # Convert contour points to spatial coordinates
        contour_coords = [src.xy(int(pt[0][1]), int(pt[0][0])) for pt in largest_contour]
        contour_polygon = Polygon(contour_coords)

    # Convert to GeoDataFrame
    return gpd.GeoDataFrame({"geometry": [contour_polygon]}, crs=src.crs)



def simplify_polygon(polygon, tolerance=5):
    """
    Simplify a polygon by reducing its vertices.
    
    Parameters:
        polygon (Polygon): Input polygon to simplify.
        tolerance (float): Tolerance for simplification. Higher values result in greater simplification.
        
    Returns:
        Polygon: Simplified polygon.
    """
    return polygon.simplify(tolerance, preserve_topology=True)



def generate_voronoi_partition(region_polygon, num_points=1):
    """
    Generate Voronoi partitioning of a region polygon using shapely's voronoi_polygons.
    
    Parameters:
        region_polygon (Polygon): The polygon defining the region to partition.
        num_points (int): Number of seed points to generate inside the polygon.

    Returns:
        GeoDataFrame: GeoDataFrame containing the clipped Voronoi polygons.
        GeoDataFrame: GeoDataFrame containing the seed points.
    """
    # Generate random points inside the region polygon
    minx, miny, maxx, maxy = region_polygon.bounds
    points = []

    # Keep adding random points in region until we hit our target number
    while len(points) < num_points:
        x, y = np.random.uniform(minx, maxx), np.random.uniform(miny, maxy)
        if region_polygon.contains(Point(x, y)):
            points.append(Point(x, y))

    # Create MultiPoint object from seed points
    multipoint = MultiPoint(points)

    # Generate Voronoi diagram
    voronoi_result = voronoi_diagram(multipoint, envelope=region_polygon, edges=False)

    # Clip Voronoi polygons to the region polygon
    clipped_polygons = [poly.intersection(region_polygon) for poly in voronoi_result.geoms]

    # Create GeoDataFrames for the Voronoi polygons and seed points
    voronoi_gdf = gpd.GeoDataFrame({"geometry": clipped_polygons}, crs="EPSG:32614")
    points_gdf = gpd.GeoDataFrame({"geometry": points}, crs="EPSG:32614")

    return voronoi_gdf, points_gdf



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

        # Compute centroids of Voronoi polygons
        new_points = []
        for poly in voronoi_result.geoms:
            clipped_poly = poly.intersection(region_polygon)
            if clipped_poly.is_valid and not clipped_poly.is_empty:
                new_points.append(clipped_poly.centroid)
        
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
    voronoi_cells_gdf['cell_centroid'] = gpd.GeoSeries(points) # Add centroids as column
    voronoi_cells_gdf['cell_id'] = range(len(voronoi_cells_gdf)) # Add an 'id' column to the Voronoi cells GeoDataFrame

    return voronoi_cells_gdf
