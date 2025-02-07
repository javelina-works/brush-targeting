from backend.models.pipeline import ProcessingStage
from backend.persistence.file_manager import load_pipeline, save_pipeline

def add_stage(project_id: str, job_id: str, technique: str, params: dict):
    pipeline = load_pipeline(project_id, job_id)
    new_stage = ProcessingStage(index=len(pipeline["stages"]), technique=technique, params=params)
    pipeline["stages"].append(new_stage.dict())
    save_pipeline(project_id, job_id, pipeline)
    return new_stage
