from pydantic import BaseModel
from typing import Dict, Optional

class ProcessingStage(BaseModel):
    index: int
    technique: str
    params: Dict[str, float]
    enabled: bool = True
    sample_output: Optional[str] = None
    full_output: Optional[str] = None
