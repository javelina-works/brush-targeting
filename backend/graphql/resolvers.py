import strawberry
from typing import Optional, List
# from backend.models.project import Project
# from backend.persistence.file_manager import load_pipeline, save_pipeline

from .types import MapAsset
from .utils import fetch_map_assets

# @strawberry.field
def get_map_assets(location_id: str, job_id: str, layers: Optional[List[str]] = None) -> list[MapAsset]:
    """
    Resolver to retrieve all assets for a given location and job.
    """
    assets = fetch_map_assets(location_id, job_id)
    
    # If layers are specified, filter only the requested types
    if layers:
        assets = [asset for asset in assets if asset["name"] in layers]

    return [MapAsset(
                id=a["id"], name=a["name"], type=a["type"], geojson=a["geojson"]) 
            for a in assets]
