from pydantic import BaseModel
from typing import List, Optional
import uuid

class BaseLocation(BaseModel):
    name: str

class LocationCreate(BaseLocation):
    pass # for CRUD input operations

class Location(BaseLocation):
    id: str # True location will have ID



class BaseJob(BaseModel):
    location_id: str
    name: str

class JobCreate(BaseJob):
    pass

class Job(BaseJob):
    id: str
    input_image_path: Optional[str] = None    

