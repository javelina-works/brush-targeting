import strawberry
from typing import Optional, List
from .types import MapAsset, GeoJSONInput, UpdateGeoJSONResponse
# from backend.models.project import Project
# from backend.persistence.file_manager import load_pipeline, save_pipeline
from .utils import fetch_map_assets, save_geojson_file

# @strawberry.field
def get_map_assets(location_id: str, job_id: str, layers: Optional[List[str]] = None) -> list[MapAsset]:
    """
    Resolver to retrieve all assets for a given location and job.
    """
    from .utils import fetch_map_assets
    
    assets = fetch_map_assets(location_id, job_id)
    if layers: # If layers are specified, filter only the requested types
        assets = [asset for asset in assets if asset["name"] in layers]

    return [MapAsset(
                id=a["id"], name=a["name"], type=a["type"], geojson=a["geojson"]) 
            for a in assets]


def update_map_assets(location_id: str, job_id: str, geojson_files: List[GeoJSONInput]) -> UpdateGeoJSONResponse:
    """
    Updates multiple GeoJSON files for a given location and job.
    Returns an UpdateGeoJSONResponse with updated assets and an error message (if any files failed).
    """
    updated_assets = []
    failed_assets = []

    for geojson_file in geojson_files:
        # TODO: raise exception if failed and pass as error message in response
        success = save_geojson_file(location_id, job_id, geojson_file.name, geojson_file.geojson)
        if success:
            updated_assets.append(geojson_file.name)
        else:
            failed_assets.append(geojson_file.name)

    # Fetch all successfully updated assets
    assets = fetch_map_assets(location_id, job_id)
    updated_assets_data = [asset for asset in assets if asset["name"] in updated_assets]

    # Create an error message if any files failed
    error_message = None
    if failed_assets:
        error_message = f"Failed to update the following files: {', '.join(failed_assets)}"
        print(f"❌ {error_message}")

    return UpdateGeoJSONResponse(
        updatedAssets=[
            MapAsset(id=a["id"], name=a["name"], type=a["type"], geojson=a["geojson"])
            for a in updated_assets_data
        ],
        errorMessage=error_message
    )