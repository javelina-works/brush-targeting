from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse, StreamingResponse
import os
import zipfile
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

def generate_zip_stream(job_dir, selected_files):
    """
    Streams the zip file instead of storing it in memory.
    - Reads files in chunks to avoid high RAM usage.
    - Yields data as the ZIP is being created.
    """
    def stream():
        with zipfile.ZipFile(io.BytesIO(), "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_name in selected_files:
                file_path = find_file_in_subdirectories(job_dir, file_name, MAX_FILE_SEARCH)

                if file_path:
                    arcname = os.path.relpath(file_path, job_dir)  # Preserve folder structure
                    zipf.write(file_path, arcname=arcname)
                else:
                    raise HTTPException(status_code=400, detail=f"File not found: {file_name}")

            # Yield ZIP data in chunks
            zipf.close()
            yield zipf.fp.getvalue()

    return stream()

@router.post("/download/{job_id}/zip")
async def download_job_files_as_zip(job_id: str, payload: dict = Body(...)):
    """
    Returns a ZIP file containing the selected files from a job directory.
    - Searches for files in any child directory up to MAX_DEPTH levels deep.
    """
    
    selected_files = payload.get("selected_files", [])
    if not isinstance(selected_files, list):
        raise HTTPException(status_code=400, detail="Invalid format: `selected_files` must be a list of file names.")
    
    data = load_data()
    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_dir = os.path.join(LOCATIONS_DIR, job["location_id"], job_id)
    if not os.path.exists(job_dir):
        raise HTTPException(status_code=404, detail="No files found for this job")

    # Validate file selection
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_name in selected_files:
            file_path = find_file_in_subdirectories(job_dir, file_name, MAX_FILE_SEARCH)

            if file_path:
                arcname = os.path.relpath(file_path, job_dir) # Maintain relative path inside ZIP
                zipf.write(file_path, arcname=arcname)
            else:
                raise HTTPException(status_code=400, detail=f"File not found: {file_name}")

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer, 
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=job_{job_id}.zip"}
    )
