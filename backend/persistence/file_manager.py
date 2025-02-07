import json
import os

def get_pipeline_path(project_id: str, job_id: str):
    return f"/media/locations/{project_id}/jobs/{job_id}/processing.json"

def load_pipeline(project_id: str, job_id: str):
    path = get_pipeline_path(project_id, job_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"stages": []}

def save_pipeline(project_id: str, job_id: str, pipeline_data):
    path = get_pipeline_path(project_id, job_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(pipeline_data, f, indent=4)
