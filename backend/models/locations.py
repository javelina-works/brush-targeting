from pydantic import BaseModel
from typing import List, Optional
import uuid

class Location(BaseModel):
    id: str
    name: str

class Job(BaseModel):
    id: str
    location_id: str
    name: str
    input_image_path: Optional[str] = None
