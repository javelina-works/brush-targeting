import strawberry
from typing import Optional, Dict, List
# from backend.models.processing import ( ParameterModel, )
# from backend.models.pipeline import ( ProcessingStage )

@strawberry.type
class GeoJSONFeatureCollection:
    type: str = "FeatureCollection"
    features: str  # Stored as a JSON string

@strawberry.input
class GeoJSONInput:
    name: str  # The name of the GeoJSON file (e.g., "approved_targets")
    geojson: str  # The GeoJSON data as a string

@strawberry.type
class MapAsset:
    id: str
    name: str
    type: str
    geojson: str  # Assuming GeoJSON is stored as a string or file path


@strawberry.type
class UpdateGeoJSONResponse:
    updatedAssets: List[MapAsset]  # List of successfully updated assets
    errorMessage: Optional[str]  # Error message if any files failed

# @strawberry.type
# class Query:
#     @strawberry.field
#     def regionOutline(self) -> Optional[GeoJSONFeatureCollection]:
#         with open("data/region_outline.geojson", "r") as f:
#             return GeoJSONFeatureCollection(features=f.read())

#     @strawberry.field
#     def cvTargets(self) -> Optional[GeoJSONFeatureCollection]:
#         with open("data/cv_targets.geojson", "r") as f:
#             return GeoJSONFeatureCollection(features=f.read())

#     @strawberry.field
#     def auditedTargets(self) -> Optional[GeoJSONFeatureCollection]:
#         with open("data/audited_targets.geojson", "r") as f:
#             return GeoJSONFeatureCollection(features=f.read())

#     @strawberry.field
#     def voronoiCells(self) -> Optional[GeoJSONFeatureCollection]:
#         with open("data/voronoi_cells.geojson", "r") as f:
#             return GeoJSONFeatureCollection(features=f.read())



# @strawberry.type
# class Mutation:
#     @strawberry.mutation
#     def create_project(self, name: str) -> Project:
#         return create_project(name)
