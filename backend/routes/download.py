from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse, StreamingResponse
import os
import zipfile
import json
import zipstream
import zipfly
import io
from backend.config import LOCATIONS_DIR, load_data, MAX_FILE_SEARCH

router = APIRouter()

# @router.get("/download/{job_id}")
# def list_job_files(job_id: str):
#     """Returns a list of files available for download within a job."""
    
#     data = load_data()
#     job = next((j for j in data["jobs"] if j["id"] == job_id), None)
#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")

#     job_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id)
    
#     if not os.path.exists(job_dir):
#         raise HTTPException(status_code=404, detail="No files found for this job")

#     # List all files in the job directory
#     file_list = []
#     for root, _, files in os.walk(job_dir):
#         for file in files:
#             relative_path = os.path.relpath(os.path.join(root, file), job_dir)
#             file_list.append(relative_path)

#     return {"job_id": job_id, "files": file_list}


def find_file_in_subdirectories(base_dir, file_name, max_depth=MAX_FILE_SEARCH):
    """
    Recursively searches for a file within `max_depth` subdirectories.
    Returns the full path if found, otherwise None.
    """
    for root, _, files in os.walk(base_dir):
        depth = root[len(base_dir):].count(os.sep)
        if depth > max_depth:
            continue  # Skip deeper directories

        if file_name in files:
            return os.path.join(root, file_name)
    
    return None  # File not found

def stream_zip(job_dir, selected_files):
    """
    Generates and streams a ZIP file in chunks instead of storing it fully in memory.
    - Uses `io.BytesIO` to buffer and stream the zip contents.
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_name in selected_files:
            file_path = find_file_in_subdirectories(job_dir, file_name, MAX_FILE_SEARCH)
            if file_path:
                arcname = os.path.relpath(file_path, job_dir)  # Maintain relative structure
                zipf.write(file_path, arcname=arcname)
            else:
                raise HTTPException(status_code=400, detail=f"File not found: {file_name}")

    zip_buffer.seek(0)  # Move pointer to start of buffer for streaming

    def iter_chunks():
        """Yields ZIP file content in chunks to stream to client."""
        while chunk := zip_buffer.read(8192):  # Read in 8KB chunks
            yield chunk

    return iter_chunks()



def stream_zip_response(job_dir, selected_files):
    """
    Uses `zipfly` to dynamically stream a ZIP file while adding files on the fly.
    - No memory buffering: data is sent as files are added.
    - Works efficiently for large files.
    """
    paths  = []

    for file_name in selected_files:
        file_path = find_file_in_subdirectories(job_dir, file_name, MAX_FILE_SEARCH)

        if file_path:
            arcname = os.path.relpath(file_path, job_dir)  # Maintain folder structure
            paths .append({"fs": file_path, "n": arcname})
        else:
            raise HTTPException(status_code=400, detail=f"File not found: {file_name}")

    # Configure ZipFly for streaming
    zip_generator = zipfly.ZipFly(paths=paths)
    # return zip_generator.generator()  # Returns a generator that streams ZIP data

    # ✅ Ensure we yield each chunk of data correctly
    def zip_stream():
        for chunk in zip_generator.generator():
            yield chunk  # ✅ Properly yield each chunk instead of ending early

    return zip_stream()




@router.get("/download/{job_id}/zip")
def download_job_files_as_zip(job_id: str, payload: str = Query(...)):
    """
    Returns a ZIP file containing the selected files from a job directory.
    - Searches for files in any child directory up to MAX_DEPTH levels deep.
    """
    
    try:
        selected_files = json.loads(payload).get("selected_files", [])
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid payload format")
    
    if not isinstance(selected_files, list):
        raise HTTPException(status_code=400, detail="Invalid format: `selected_files` must be a list of file names.")
    
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id)
    if not os.path.exists(job_dir):
        raise HTTPException(status_code=404, detail="No files found for this job")

    # zip_generator = stream_zip_response(job_dir, selected_files)

    return StreamingResponse(
        stream_zip_response(job_dir, selected_files),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=job_{job_id}.zip",
            "Transfer-Encoding": "chunked",  # Ensures true streaming
        }
    )
