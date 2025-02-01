import param
import json
import numpy as np
from pathlib import Path
import os
from .project import Project

class StageArtifactManager(param.Parameterized):
    """Manages input/output files for a specific pipeline stage using Param."""
    project = param.ClassSelector(class_=Project, doc="Reference to the current project")
    stage_name = param.String(doc="Name of the pipeline stage")
    
    input_files = param.List(default=[], doc="List of required input files")
    stage_output_dir_name = param.Foldername(default='outputs', check_exists=False, doc="Path to stage-specific output directory")
    output_files = param.List(default=[], instantiate=True, doc="List of expected output files")
    
    has_required_inputs = param.Boolean(default=False, doc="Whether all required inputs are present")
    has_required_outputs = param.Boolean(default=False, doc="Whether all required outputs are present")

    def __init__(self, **params):
        super().__init__(**params)

        try:
            # Define input/output directories for this stage
            self.stage_output_dir = Path(self.project.project_dir) / (self.stage_output_dir_name or f"outputs")
            self.stage_output_dir.mkdir(parents=True, exist_ok=True)

            # Store full paths for input/output files
            self.input_files = [Path(self.project.project_dir) / file for file in self.input_files]
            self.output_files = [self.stage_output_dir / file for file in self.output_files]
        except Exception as e:
            print(f"Error initializing SAM for stage {self.stage_name}: {e}")

        self._validate_inputs_exist() # Check if required inputs exist
        self._update_output_status() # Check output status on init

    def get_file_handle(self, filename):
        """Return a valid file handle (path) if the file exists and is registered as an input or output."""
        
        # Check if filename is in the known input/output list
        input_paths = {str(Path(self.project.project_dir) / file): Path(self.project.project_dir) / file for file in self.input_files}
        output_paths = {file.name: self.stage_output_dir / file.name for file in self.output_files}

        # print(f"Requested file: {filename}")
        # print(f"Input paths: {input_paths}")
        # print(f"Output paths: {output_paths}")

        requested_input_path = str(Path(self.project.project_dir) / filename)
        requested_output_path = filename  # Plain filename should match output files

        # Determine if it's an input or output file
        if requested_input_path in input_paths:
            path = input_paths[requested_input_path]
        elif requested_output_path in output_paths:
            path = output_paths[requested_output_path]
        else:
            raise ValueError(f"Requested file '{filename}' is not a defined input or output for stage '{self.stage_name}'.")

        # Return the file path only if it exists
        # return path if path.exists() else None
        return path
    


    def _validate_inputs_exist(self):
        """Raises an error if any required input file is missing."""
        missing_files = [str(f) for f in self.input_files if not f.exists()]
        if missing_files:
            raise FileNotFoundError(f"Missing required input files for stage '{self.stage_name}': {missing_files}")
        else:
            print("All expected inputs present")
            self.has_required_inputs = True

    @param.depends("input_files", watch=True)
    def _update_input_status(self):
        self.has_required_inputs = all(f.exists() for f in self.input_files)

    @param.depends("output_files", watch=True)
    def _update_output_status(self):
        self.has_required_outputs = all(f.exists() for f in self.output_files)

    # def save_artifact(self, filename, data):
    #     """Save an artifact to the stage's output directory, handling different formats."""
    #     path = self.stage_output_dir / filename
    #     os.makedirs(path.parent, exist_ok=True)

    #     if isinstance(data, np.ndarray):
    #         np.save(path, data)
    #     elif isinstance(data, dict):
    #         with open(path, "w") as f:
    #             json.dump(data, f)
    #     elif isinstance(data, str) or isinstance(data, bytes):
    #         mode = "w" if isinstance(data, str) else "wb"
    #         with open(path, mode) as f:
    #             f.write(data)
    #     else:
    #         raise ValueError(f"Unsupported data type for {filename}")

    #     self._update_output_status() # Check output status after saving


    # def get_artifact(self, filename):
    #     """Retrieve an artifact from the stage’s output directory."""
    #     path = self.stage_output_dir / filename
    #     if not path.exists():
    #         return None

    #     if filename.endswith(".npy"):
    #         return np.load(path)
    #     elif filename.endswith(".json"):
    #         with open(path, "r") as f:
    #             return json.load(f)
    #     elif filename.endswith(".txt"):
    #         with open(path, "r") as f:
    #             return f.read()
    #     else:
    #         return path.read_bytes()  # Generic binary file


'''
# Example usage of StageArtifactManager
self.artifact_manager = StageArtifactManager(
        project=self.project,
        stage_name="search",
        input_files=["input/input_image.jpg", "input/region.geojson", "search/binary_mask.npy"],
        stage_output_dir_name="target_search"  # Store uploads in `input/upload/`
        output_files=["targets.geojson", "region_outline.geojson"],
    )
'''

