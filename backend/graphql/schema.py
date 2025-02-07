import strawberry
from graphql.types import Query, Mutation

schema = strawberry.Schema(query=Query, mutation=Mutation)
