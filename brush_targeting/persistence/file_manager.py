import os
import param

# TODO: may just get rid of this. Seems like better handled in Project, ProjectManager

class FileManager(param.Parameterized):
    media_dir = param.String(default=os.getenv("MEDIA_DIR", "media"))
    projects_dir = param.String(default=None, precedence=-1)
    temp_dir = param.String(default=None, precedence=-1)

    def __init__(self, **params):
        super().__init__(**params)
        self.projects_dir = os.path.join(self.media_dir, "projects")
        self.temp_dir = os.path.join(self.media_dir, "temp")
        self.initialize_directories()

    def initialize_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    def list_projects(self):
        """List all project directories."""
        if not os.path.exists(self.projects_dir):
            return []
        return [d for d in os.listdir(self.projects_dir) if os.path.isdir(os.path.join(self.projects_dir, d))]

    def project_exists(self, project_name):
        """Check if a project already exists."""
        return os.path.exists(os.path.join(self.projects_dir, project_name))
