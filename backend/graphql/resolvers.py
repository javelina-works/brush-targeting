# from backend.models.project import Project
# from backend.persistence.file_manager import load_pipeline, save_pipeline
# from typing import Optional, List

from .types import MapAsset
from .utils import fetch_map_assets
import strawberry

# @strawberry.field
def get_map_assets(location_id: str, job_id: str) -> list[MapAsset]:
    """
    Resolver to retrieve all assets for a given location and job.
    """
    assets = fetch_map_assets(location_id, job_id)
    
    return [MapAsset(
                id=a["id"], name=a["name"], 
                type=a["type"], geojson=a["geojson"]) 
            for a in assets]
