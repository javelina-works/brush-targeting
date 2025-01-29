import param
import os
from .file_manager import FileManager

class ProjectManager(FileManager):
    current_project = param.String(default="", doc="Currently selected project")

    def create_project(self, project_name):
        """Create a new project directory structure."""
        project_name = project_name.strip()
        if not project_name:
            raise ValueError("Project name cannot be empty.")

        project_path = os.path.join(self.projects_dir, project_name)

        if self.project_exists(project_name):
            raise FileExistsError(f"Project '{project_name}' already exists.")

        os.makedirs(os.path.join(project_path, "inputs"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "target"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "routes"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "outputs"), exist_ok=True)

        return project_path

    def set_current_project(self, project_name):
        """Set the active project if it exists."""
        if not self.project_exists(project_name):
            raise FileNotFoundError(f"Project '{project_name}' does not exist.")
        
        self.current_project = project_name
