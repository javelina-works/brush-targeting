import numpy as np

def calculate_all_rgb_indices(image):
    """
    Calculate all vegetation indices for the given 3 band RGB image.
    
    Parameters:
    - image: RGB image (H, W, 3).
    
    Returns:
    - A dictionary containing all vegetation indices.
    """
    r, g, b = normalize_rgb(image)
    
    indices = {
        "ExG":  calculate_exg(r, g, b),
        "GLI":  calculate_gli(r, g, b),
        "NDI":  calculate_ndi(r, g),
        "VARI": calculate_vari(r, g, b),
        "TVI":  calculate_tvi(r ,g, b)
    }
    
    return indices


# Helper to ensure values are in the correct range [-1,1]
def normalize_rgb(image):
    """
    Normalize RGB channels to the range [0, 1].
    
    Parameters:
    - image: RGB image (H, W, 3).
    
    Returns:
    - r, g, b: Normalized red, green, and blue channels.
    """
    return image[:, :, 0] / 255.0, image[:, :, 1] / 255.0, image[:, :, 2] / 255.0


def calculate_exg(r, g, b):
    """
    Calculate Excess Green Index (ExG).
    
    Parameters:
    - r, g, b: Normalized red, green, and blue channels (0 to 1).
    
    Returns:
    - ExG index.
    """
    return 2 * g - r - b

def calculate_gli(r, g, b):
    """
    Calculate Green Leaf Index (GLI).
    
    Parameters:
    - r, g, b: Normalized red, green, and blue channels (0 to 1).
    
    Returns:
    - GLI index.
    """
    return (2 * g - r - b) / (2 * g + r + b + 1e-5)  # Avoid division by zero

def calculate_ndi(r, g):
    """
    Calculate Normalized Difference Index (NDI).
    
    Parameters:
    - r, g: Normalized red and green channels (0 to 1).
    
    Returns:
    - NDI index.
    """
    ndi = (g - r) / (g + r + 1e-5)  # Avoid division by zero
    return ndi 

def calculate_vari(r, g, b):
    """
    Calculate Visible Atmospherically Resistant Index (VARI).
    
    Parameters:
    - r, g, b: Normalized red, green, and blue channels (0 to 1).
    
    Returns:
    - VARI index.
    """
    vari = (g - r) / (g + r - b + 1e-5)  # Avoid division by zero
    # vari_normalized = (vari - np.min(vari)) / (np.max(vari) - np.min(vari) + 1e-5)
    return np.clip(vari, -1, 1)
    return vari_normalized

def calculate_tvi(r, g, b):
    """
    Calculate Triangular Vegetation Index (TVI).
    
    Parameters:
    - r, g, b: Normalized red, green, and blue channels (0 to 1).
    
    Returns:
    - TVI index.
    """
    tvi = 0.5 * (120 * (g - r) - 200 * (b - r))
    tvi_normalized = (tvi - np.min(tvi)) / (np.max(tvi) - np.min(tvi) + 1e-5)
    return tvi_normalized