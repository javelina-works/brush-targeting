from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from PIL import Image
from io import BytesIO
import os
import time
import logging

import strawberry
from strawberry.fastapi import GraphQLRouter

from backend.graphql.schema import schema
from backend.routes import (
    locations, jobs, upload, download, files, 
    pipeline, targets, tiles, image_search, waypoints
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get allowed frontend origin from environment variable
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:8000")  # Default for local dev

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
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
    allow_credentials=True,
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=100_000, # Compress responses >100KB
)  

# Debugging response times of requests on server
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()  # ⏳ Start timing
    response = await call_next(request)
    elapsed_time = time.time() - start_time  # ⏱ Calculate duration

    logger.info(f"{request.method} {request.url.path} - {elapsed_time:.3f}s")
    return response


# Mount GraphQL API
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# Register routers
app.include_router(locations.router, prefix="/api") # General locations, equivalent to a project
app.include_router(jobs.router, prefix="/api")  # Jobs at a location. Organizes jobs for each project
app.include_router(upload.router, prefix="/api") # Handles file uploads to server
app.include_router(download.router, prefix="/api") # Handles file downloads from server
app.include_router(files.router, prefix="/api") # Handles file retreival
app.include_router(tiles.router, prefix="/api") # Tile generation and serving

app.include_router(targets.router, prefix="/api") # Handle targets associated with a job
app.include_router(pipeline.router, prefix="/api")
app.include_router(image_search.router, prefix="/api") # Temporary API for image search
app.include_router(waypoints.router, prefix="/api") # Generate output waypoint files


# Serve static files from the Vue build directory
"""
Vue frontend static asset routing:
In a nutshell, if FastAPI cannot find the route (unmatched), we send it to the Vue frontend.
Since Vue handles routing on the client side, we just return index.html for any unmatched route.
Once Vue gets the path, it will decide the correct page to produce. 

That is also why the following does not work:
`app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")`
"""
# if os.getenv("ENV") == "production":
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="static")

@app.get("/{full_path:path}")
async def serve_vue_app(full_path: str):
    """Catch-all route to serve Vue index.html"""
    return FileResponse("frontend/dist/index.html")


# @app.get("/")
# async def root():
#     return {"message": "Go to /graphql for the GraphQL API"}
