import strawberry
from typing import List, Optional, Dict
from backend.models.pipeline import ProcessingStage

@strawberry.type
class Project:
    id: str
    name: str
    jobs: List[str]

@strawberry.type
class Query:
    @strawberry.field
    def project(self, id: str) -> Optional[Project]:
        return get_project(id)

    @strawberry.field
    def list_projects(self) -> List[Project]:
        return list_projects()

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_project(self, name: str) -> Project:
        return create_project(name)
