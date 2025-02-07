from pydantic import BaseModel
from typing import List, Optional

class ParameterModel(BaseModel):
    name: str
    type: str
    min: Optional[float] = None
    max: Optional[float] = None
    default: Optional[float] = None

class Technique(BaseModel):
    pass

class ProcessingStage(BaseModel):
    id: str
    job_id: str
    technique: str
    parameters: dict
    enabled: bool = True
