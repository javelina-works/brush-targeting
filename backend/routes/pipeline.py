from fastapi import APIRouter, HTTPException
import uuid
from backend.models.pipeline import PipelineCreate, Pipeline, StageCreate
from backend.config import load_pipelines, save_pipelines

router = APIRouter()


# Simple function registry (for now)
FUNCTION_REGISTRY = {
    "stage1": lambda img: img + "_processed1",
    "stage2": lambda img: img + "_processed2",
    "stage3": lambda img: img + "_processed3"
}


# [CREATE] pipeline
@router.post("/pipelines", status_code=201, response_model=Pipeline)
def create_pipeline(pipeline: PipelineCreate):
    pipelines_data = load_pipelines()
    new_pipeline = Pipeline(id=str(uuid.uuid4()), name=pipeline.name)

    pipelines_data['pipelines'].append(new_pipeline.model_dump())
    save_pipelines(pipelines_data)

    return new_pipeline


# [READ] pipeline
@router.get("/pipelines/{pipeline_id}")
def get_pipeline(pipeline_id: str):
    pipelines_data = load_pipelines()
    pipeline = next((pipe for pipe in pipelines_data["pipelines"] if pipe["id"] == pipeline_id), None)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return pipeline


# [DELETE] pipeline
@router.delete("/pipelines/{pipeline_id}")
def delete_pipeline(pipeline_id: str):
    pipelines_data = load_pipelines()

    pipeline = next((pipe for pipe in pipelines_data["pipelines"] if pipe["id"] == pipeline_id), None)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    pipelines_data['pipelines'] = [pipe for pipe in pipelines_data['pipelines'] 
                                   if pipe['id'] != pipeline_id]
    save_pipelines(pipelines_data)
    return {"message": "Pipeline deleted"}


# [LIST] pipelines
@router.get("/pipelines")
def list_pipelines():
    pipelines_data = load_pipelines()
    return pipelines_data["pipelines"]


# [ADD STAGE] to pipeline
@router.post("/pipelines/{pipeline_id}/stages", status_code=201)
def add_stage(pipeline_id: str, stage: StageCreate):
    pipelines_data = load_pipelines()
    pipeline = next((pipe for pipe in pipelines_data["pipelines"] if pipe["id"] == pipeline_id), None)

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if stage.function not in FUNCTION_REGISTRY:
        raise HTTPException(status_code=400, detail="Invalid function name")

    stage_id = str(uuid.uuid4())
    new_stage = {"id": stage_id, "function": stage.function}
    pipeline["stages"].append(new_stage)
    save_pipelines(pipelines_data)

    return new_stage


# [LIST] stages in a pipeline
@router.get("/pipelines/{pipeline_id}/stages")
def list_stages(pipeline_id: str):
    pipelines_data = load_pipelines()
    pipeline = next((pipe for pipe in pipelines_data["pipelines"] if pipe["id"] == pipeline_id), None)

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return pipeline["stages"]


# [UPDATE] stage function
@router.patch("/pipelines/{pipeline_id}/stages/{stage_id}")
def update_stage(pipeline_id: str, stage_id: str, stage: StageCreate):
    pipelines_data = load_pipelines()
    pipeline = next((pipe for pipe in pipelines_data["pipelines"] if pipe["id"] == pipeline_id), None)

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if stage.function not in FUNCTION_REGISTRY:
        raise HTTPException(status_code=400, detail="Invalid function name")

    for s in pipeline["stages"]:
        if s["id"] == stage_id:
            s["function"] = stage.function
            s["name"] = stage.name
            save_pipelines(pipelines_data)
            return s

    raise HTTPException(status_code=404, detail="Stage not found")


# [DELETE] a stage from a pipeline
@router.delete("/pipelines/{pipeline_id}/stages/{stage_id}")
def remove_stage(pipeline_id: str, stage_id: str):
    pipelines_data = load_pipelines()
    pipeline = next((pipe for pipe in pipelines_data["pipelines"] if pipe["id"] == pipeline_id), None)

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline["stages"] = [s for s in pipeline["stages"] if s["id"] != stage_id]
    save_pipelines(pipelines_data)

    return {"message": "Stage removed"}


# [RUN] the pipeline on an image
@router.post("/pipelines/{pipeline_id}/run")
def run_pipeline(pipeline_id: str, image: str):
    pipelines_data = load_pipelines()
    pipeline = next((pipe for pipe in pipelines_data["pipelines"] if pipe["id"] == pipeline_id), None)

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    result = image
    for stage in pipeline["stages"]:
        func = FUNCTION_REGISTRY.get(stage["function"])
        if func:
            result = func(result)

    return {"pipeline_id": pipeline_id, "result": result}