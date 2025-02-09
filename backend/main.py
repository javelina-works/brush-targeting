from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
# from strawberry.fastapi import GraphQLRouter
# from graphql.schema import schema
from PIL import Image
from io import BytesIO
from backend.routes import locations, jobs, upload, pipeline


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Setup tasks for the FastAPI application.
    """
    global TRANSPARENT_TILE

    # Generate the transparent tile during startup
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))  # Transparent RGBA image
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    TRANSPARENT_TILE = buffer.getvalue()
    # Lifespan enter (app startup)
    yield
    # Lifespan exit (app shutdown)
    TRANSPARENT_TILE = None  # Clean up the cached tile if needed

app = FastAPI(lifespan=app_lifespan)

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000", "*"],  # Allow only your frontend origin
#     allow_methods=["GET", "POST"],  # Allow all HTTP methods (GET, POST, etc.)
#     allow_headers=["*"],  # Allow all headers
#     allow_credentials=True,
# )


# graphql_app = GraphQLRouter(schema)
# app.include_router(graphql_app, prefix="/graphql")

# Register routers
app.include_router(locations.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")

# # Serve static files from the Vue build directory
# app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")


@app.get("/")
async def root():
    return {"message": "Go to /graphql for the GraphQL API"}
