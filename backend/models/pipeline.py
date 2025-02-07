from pydantic import BaseModel
from typing import Dict, Optional, List

class BaseStage(BaseModel):
    name: str
    function: str

class StageCreate(BaseStage):
    pass

class Stage(BaseStage):
    id: str # ID of a given stage

class ProcessingStage(BaseModel):
    index: int
    technique: str
    params: Dict[str, float]
    enabled: bool = True
    sample_output: Optional[str] = None
    full_output: Optional[str] = None



class BasePipeline(BaseModel):
    name: str

class PipelineCreate(BasePipeline):
    pass

class Pipeline(BasePipeline):
    id: str # each pipeline will need to have an ID
    stages: Optional[List[StageCreate]] = []


