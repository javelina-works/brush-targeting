from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from PIL import Image
from io import BytesIO

import strawberry
from strawberry.fastapi import GraphQLRouter

from backend.graphql.schema import schema
from backend.routes import locations, jobs, upload, files, pipeline, targets, tiles, image_search


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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173", "*"],  # Allow only your frontend origin
    allow_origins=["*"],  # Allow only your frontend origin
    allow_methods=["GET", "POST", "DELETE"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
    allow_credentials=True,
)

# Mount GraphQL API
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# Register routers
app.include_router(locations.router, prefix="/api") # General locations, equivalent to a project
app.include_router(jobs.router, prefix="/api")  # Jobs at a location. Organizes jobs for each project
app.include_router(upload.router, prefix="/api") # Handles file uploads to server
app.include_router(files.router, prefix="/api") # Handles file retreival
app.include_router(tiles.router, prefix="/api") # Tile generation and serving

app.include_router(targets.router, prefix="/api") # Handle targets associated with a job
app.include_router(pipeline.router, prefix="/api")
app.include_router(image_search.router, prefix="/api") # Temporary API for image search


# # Serve static files from the Vue build directory
# app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")


@app.get("/")
async def root():
    return {"message": "Go to /graphql for the GraphQL API"}
