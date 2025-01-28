import matplotlib.pyplot as plt
import rasterio
import cv2
import os

# Load an image (GeoTIFF or standard formats)
def load_image(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
        if file_path.endswith('.tif'):
            # Use rasterio for GeoTIFFs
            with rasterio.open(file_path) as src:
                print(f"Image CRS - {src.crs}")
                image = src.read([b for b in range(1, src.count + 1)]).transpose(1, 2, 0) # RGB(A)
                return image, src.transform, src.bounds, src.crs
        else:
            # Use OpenCV or PIL for standard formats
            image = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB)
            return image, None, None, None
    except Exception as e:
        print(f"Error loading image: {e}")
        return None, None, None, None

# Visualize the image
def plot_image(image, title="Image"):
    plt.figure(figsize=(10, 8))
    plt.imshow(image)
    plt.title(title)
    # plt.axis('off')
    plt.show()

# Visualize the image in geographic context
def plot_geotiff(image, transform, bounds, title="GeoTIFF"):
    if transform is None or bounds is None:
        print("Geographic data unavailable; displaying image with pixel coordinates.")
        plot_image(image, title)
        return
    
    # Create figure with geographic extent
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Calculate extent in geographic coordinates
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
    
    # Display the image with geographic extent
    ax.imshow(image, extent=extent)
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.show()