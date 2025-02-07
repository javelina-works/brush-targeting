from pydantic import BaseModel
from typing import List

class Project(BaseModel):
    id: str
    name: str
    jobs: List[str]  # List of job IDs under this project
