from fastapi import FastAPI
# from strawberry.fastapi import GraphQLRouter
# from graphql.schema import schema
from backend.routes import locations, jobs

app = FastAPI()

# graphql_app = GraphQLRouter(schema)
# app.include_router(graphql_app, prefix="/graphql")


app.include_router(locations.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Go to /graphql for the GraphQL API"}
