from backend.models.project import Project
from backend.persistence.file_manager import load_pipeline, save_pipeline
from typing import Optional, List

# Mocked storage (replace with database or file persistence)
PROJECTS = {}

def get_project(id: str) -> Optional[Project]:
    return PROJECTS.get(id)

def create_project(name: str) -> Project:
    project = Project(id=name, name=name, jobs=[])
    PROJECTS[name] = project
    return project

def list_projects() -> List[Project]:
    return list(PROJECTS.values())
