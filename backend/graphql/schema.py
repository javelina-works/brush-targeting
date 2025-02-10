import strawberry
from .resolvers import get_map_assets
from .types import MapAsset
# from .types import Query, Mutation

def get_name() -> str:
    return "Strawberry"

@strawberry.type
class Query:
    mapAssets: list[MapAsset] = strawberry.field(resolver=get_map_assets)



schema = strawberry.Schema(query=Query)