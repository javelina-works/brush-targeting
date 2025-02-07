from pydantic import BaseModel
from typing import List, Optional

class ProcessingStage(BaseModel):
    id: str
    job_id: str
    technique: str
    parameters: dict
    enabled: bool = True
