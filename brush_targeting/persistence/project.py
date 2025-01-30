import param
import os
import json
import shutil
import re


def validate_project_name(name):
    """Ensures a project name is safe for use as a folder name."""
    if not name or not name.strip():
        raise ValueError("Project name cannot be empty or only whitespace.")

    # Ensure project name contains only valid characters
    if re.search(r'[<>:"/\\|?*]', name):
        raise ValueError(f"Invalid project name '{name}'. Avoid special characters.")

    return name.strip()



class Project(param.Parameterized):
    """
    Manages project directories, artifacts, and metadata.
    By default, will create `inputs` and `outputs` directories, although may create more.
    """

    name = param.String(doc="Project name", allow_None=False)
    project_dir = param.Foldername(doc="Base directory where the project's contents are stored")

    def __init__(self, name, project_dir, **params):
        super().__init__(name=name, project_dir=os.path.abspath(project_dir), **params)

        self.inputs_dir = os.path.join(self.project_dir, "inputs")
        self.outputs_dir = os.path.join(self.project_dir, "outputs")
        self.metadata_path = os.path.join(self.project_dir, "metadata.json")

        self.load_metadata()  # Load existing metadata (ProjectManager ensures it exists)

    def save_file(self, uploaded_file, subdir="inputs"):
        """Saves an uploaded file to the project's inputs or outputs directory."""
        target_dir = self.inputs_dir if subdir == "inputs" else self.outputs_dir
        target_path = os.path.join(target_dir, uploaded_file.name)

        with open(target_path, "wb") as f:
            shutil.copyfileobj(uploaded_file, f)

        self.save_metadata()  # Update metadata after adding a file
        return target_path

    def list_artifacts(self, subdir="outputs"):
        """Returns a list of files in the inputs or outputs directory."""
        target_dir = self.inputs_dir if subdir == "inputs" else self.outputs_dir
        return [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]

    def get_artifact_path(self, filename, subdir="outputs"):
        """Gets the full path to a stored artifact."""
        target_dir = self.inputs_dir if subdir == "inputs" else self.outputs_dir
        return os.path.join(target_dir, filename)

    def save_metadata(self):
        """Saves project metadata to a JSON file."""
        metadata = {
            "name": self.name,
            "inputs": self.list_artifacts("inputs"),
            "outputs": self.list_artifacts("outputs"),
        }
        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)

    def load_metadata(self):
        """Loads metadata from the saved JSON file."""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        return {}

    def __repr__(self):
        return f"Project(name={self.name}, directory={self.project_dir})"



class ProjectManager(param.Parameterized):
    """
    Handles project creation, retrieval, and deletion.
    Ensures project directories are valid before instantiating Project objects.
    """
    
    media_dir = param.String(default=os.getenv("MEDIA_DIR", "media"))
    projects_dir = param.Foldername(default=None, precedence=-1)
    temp_dir = param.Foldername(default=None, precedence=-1)

    def __init__(self, **params):
        super().__init__(**params)
        self.projects_dir = os.path.abspath(os.path.join(self.media_dir, "projects"))
        self.temp_dir = os.path.abspath(os.path.join(self.media_dir, "temp"))
        self.initialize_directories()

    def initialize_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    def create_project(self, name):
        """Creates a new project, ensuring directory and metadata are set up."""
        name = validate_project_name(name)
        project_path = os.path.join(self.projects_dir, name)
        
        if os.path.exists(project_path):
            raise FileExistsError(f"Project '{name}' already exists.")

        # Create project directories
        os.makedirs(project_path, exist_ok=True)
        os.makedirs(os.path.join(project_path, "inputs"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "outputs"), exist_ok=True)

        # Initialize metadata.json
        metadata_path = os.path.join(project_path, "metadata.json")
        if not os.path.exists(metadata_path):
            with open(metadata_path, "w") as f:
                json.dump({"name": name, "inputs": [], "outputs": []}, f, indent=4)

        return Project(name, project_path)  # Now project_path is guaranteed to be valid

    def load_project(self, name):
        """Loads an existing project."""
        name = validate_project_name(name)
        project_path = os.path.join(self.projects_dir, name)
        
        if not os.path.exists(project_path):
            raise FileNotFoundError(f"Project '{name}' does not exist.")
        
        return Project(name, project_path)  # No need to create directory, it must exist

    def delete_project(self, name):
        """Deletes a project and all its files."""
        name = validate_project_name(name)
        project_path = os.path.join(self.projects_dir, name)
        
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
        else:
            raise FileNotFoundError(f"Project '{name}' does not exist.")

    def list_projects(self):
        """List all project directories."""
        if not os.path.exists(self.projects_dir):
            return []
        return [d for d in os.listdir(self.projects_dir) if os.path.isdir(os.path.join(self.projects_dir, d))]

    def project_exists(self, project_name):
        """Check if a project already exists."""
        return os.path.exists(os.path.join(self.projects_dir, validate_project_name(project_name)))

