from fastapi import APIRouter
from fastapi.responses import JSONResponse, FileResponse
import os

MEDIA_DIR = "media"
os.makedirs(MEDIA_DIR, exist_ok=True)

router = APIRouter()

@router.get("/list_files")
def list_files():
    """Lists all files in the media directory."""
    files = os.listdir(MEDIA_DIR)
    return JSONResponse(content={"files": files})

@router.get("/get_file/{filename}")
def get_file(filename: str):
    """Serves a file from media directory."""
    file_path = os.path.join(MEDIA_DIR, filename)
    if not os.path.exists(file_path):
        return JSONResponse(content={"error": "File not found"}, status_code=404)
    return FileResponse(file_path)
