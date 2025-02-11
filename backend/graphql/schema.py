import strawberry
from .resolvers import get_map_assets, update_map_assets
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

schema = strawberry.Schema(query=Query, mutation=Mutation)