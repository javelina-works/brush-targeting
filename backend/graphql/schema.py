import strawberry
from .resolvers.map_assets import get_map_assets, update_map_assets
from .resolvers.tesselation import generate_region_tesselation
from .resolvers.depots import generate_depots
from .resolvers.routing import solve_job_routes
from .types import MapAsset, UpdateGeoJSONResponse
# from .types import Query, Mutation

def get_name() -> str:
    return "Strawberry"

@strawberry.type
class Query:
    mapAssets: list[MapAsset] = strawberry.field(resolver=get_map_assets)

@strawberry.type
class Mutation:
    updateMapAssets: UpdateGeoJSONResponse = strawberry.field(resolver=update_map_assets) 
    generateTesselation: MapAsset = strawberry.field(resolver=generate_region_tesselation)
    generateDepots: MapAsset = strawberry.field(resolver=generate_depots)
    solveRoutes: MapAsset = strawberry.field(resolver=solve_job_routes)

schema = strawberry.Schema(query=Query, mutation=Mutation)