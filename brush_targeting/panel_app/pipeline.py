import param
import panel as pn
import json
import shutil
import hashlib
from io import BytesIO


from brush_targeting.persistence.project import Project
from brush_targeting.persistence.pipeline_manager import StageArtifactManager

from .stage_select import ProjectManagerWidget
from .upload_stage import UploadRegionFiles
from .search_stage import *
from .search_techniques import (
    VegetationIndex, Smoothing, ContrastEnhancement, MorphologicalRefinement, ManualThresholding
)
from .utils import DownloadGeoJSON
from .targets_stage import AcquireTargetsWidget
from .stage_audit import MapView


class StageSelect(param.Parameterized):
    def __init__(self, **params):
        super().__init__(**params)
        self.project_select = ProjectManagerWidget()

    @param.output( project=param.ClassSelector(class_=Project) )
    def output(self):
        return self.project_select.selected_project

    def panel(self):
        select_row = pn.Row(
            self.project_select.panel(), # NOTE: MUST call panel() not panel to reduce flicker
        )
        return select_row


class StageUpload(param.Parameterized):
    project = param.ClassSelector(class_=Project, doc="Pipeline's current project")
    ready_to_proceed = param.Boolean(default=False, doc="Indicates if the stage can proceed")
    artifact_manager = param.Parameter( doc="Manages own artifacts.")

    def __init__(self, **params):
        super().__init__(**params)

        # Define the Artifact Manager for the Upload Stage
        self.artifact_manager = StageArtifactManager(
            project=self.project,
            stage_name="upload",
            input_files=[],  # No required inputs for this stage
            stage_output_dir_name="inputs",  # Store outputs in `inputs/`
            output_files=[
                "region_orthophoto.tif",
                "region_outline.geojson"
            ],
        )

        # Load inputs as needed
        #   -> If we got here, all inputs are known to exist
        #   -> No inputs for this stage

        # Check if outputs are already present
        if self.artifact_manager.has_required_outputs:
            print("Pre-loading required outputs!")
            try:
                preloaded_image = self.artifact_manager.get_file_handle("region_orthophoto.tif")
                preloaded_geojson = self.artifact_manager.get_file_handle("region_outline.geojson")

                if preloaded_image:
                    with open(preloaded_image, "rb") as f:
                        region_image_bytes = BytesIO(f.read())
                if preloaded_geojson:
                    with open(preloaded_geojson, "r", encoding="utf-8") as f:
                        region_geojson_dict = json.load(f)

                self.upload_widgets = UploadRegionFiles(
                    region_image_bytes = region_image_bytes,
                    region_geojson_dict = region_geojson_dict
                )
            except Exception as e:
                print(f"Error preloading stage files: {e}")
                self.upload_widgets = UploadRegionFiles() # Add UI Widgets

        else:
            print("No files found. Default init.")
            self.upload_widgets = UploadRegionFiles() # Add UI Widgets

    @param.depends("artifact_manager.has_required_outputs", watch=True)
    def _update_ready_status(self, event=None):
        """Updates readiness status based on input and output availability."""
        self.ready_to_proceed = self.artifact_manager.has_required_outputs

    @param.output( project=param.ClassSelector(class_=Project) )
    def output(self):
        # Save artifacts using the Artifact Manager
        try:
            region_geojson_dict = self.upload_widgets.region_geojson_dict
            region_outline_handle = self.artifact_manager.get_file_handle("region_outline.geojson")       
            if region_outline_handle:
                with open(region_outline_handle, 'w', encoding="utf-8") as f:
                    json.dump(region_geojson_dict, f, indent=4)

            region_orthophoto_bytes = self.upload_widgets.region_image_bytes
            region_image_handle = self.artifact_manager.get_file_handle("region_orthophoto.tif")   
            if region_image_handle:
                with open(region_image_handle, 'wb') as out_file:
                    out_file.write(region_orthophoto_bytes.getbuffer())
        except Exception as e:
                print(f"Error saving stage artifacts: {e}")
                return None
        return (self.project)
    

    def panel(self):
        return pn.Column(
            pn.indicators.BooleanStatus(
                value=self.ready_to_proceed,
                name="Ready to Proceed"
            ),
            self.upload_widgets.view(),  # UI for file uploads
        )
    


class StageSearch(param.Parameterized):
    project = param.ClassSelector(class_=Project, doc="Pipeline's current project")
    input_image = param.Parameter(allow_None=True, doc="Original region orthophoto")
    input_image_transform=param.Parameter(allow_None=True, doc="Transform to map image np.ndarray to geospatial reference")
    region_geojson = param.Parameter(default=None, doc="Uploaded geoJSON of work region outline")

    def __init__(self, **params):
        super().__init__(**params)
        if self.input_image is not None:
            self.image_array = np.array(self.input_image) # Needs to be numpy array
        else:
            self.image_array = None # Don't pass empty array
            print("Need an input image!")
            raise ValueError("input_image cannot be None in StageSearch initialization")
        self._add_search_widgets()

    @param.output(
        input_image=param.Parameter,
        input_image_transform=param.Parameter,
        binary_mask=param.Parameter,
        region_geojson=param.Parameter
    )
    def output(self):
        return self.input_image, self.input_image_transform, self.target_search.output_image, self.region_geojson
    
    def _add_search_widgets(self):
        veg_index = VegetationIndex()
        smoothing = Smoothing()
        contrast = ContrastEnhancement(enabled=False)
        morphological = MorphologicalRefinement(enabled=False)
        thresholding = ManualThresholding()
        
        self.target_search = TargetSearch(
            input_image=self.image_array,
            techniques=[veg_index, smoothing, contrast, morphological, thresholding]
        )

    def panel(self):
        search_row = pn.Row(self.target_search.view)
        return search_row
    


class StageAcquireTargets(param.Parameterized):
    input_image = param.Parameter(allow_None=False, doc="Original region orthophoto")
    input_image_transform=param.Parameter(allow_None=False, doc="Transform to map image np.ndarray to geospatial reference")
    binary_mask = param.Parameter(default=None, doc="2D np.array of binary mask")
    region_geojson = param.Parameter(default=None, doc="Uploaded geoJSON of work region outline")


    def __init__(self, **params):
        super().__init__(**params)
        self._add_aquire_targets_widgets()

        self.download_targets = DownloadGeoJSON(
            source_gdf=self.acquire_targets.targets_gdf,
            filename="targets.geojson",
            button_type="primary",
            name="Download Targets"
        )

    @param.output(
        targets_gdf=param.Parameter,
        region_geojson=param.Parameter
    )
    def output(self):
        return (
            self.acquire_targets.targets_gdf,
            self.region_geojson
        )
    
    def _add_aquire_targets_widgets(self):
        self.acquire_targets = AcquireTargetsWidget(
            binary_mask=self.binary_mask,
            input_image_transform=self.input_image_transform
        )

    def panel(self):
        if self.acquire_targets.targets_gdf is not None:
            targets_pane = f"Total targets found: {len(self.acquire_targets.targets_gdf)}"
        else:
            targets_pane = pn.pane.Markdown("No targets yet found!")

        targets_row = pn.Row(
            self.acquire_targets.view,
            self.download_targets.download_widget,
            targets_pane
        )
        return pn.panel(targets_row)



class StageAudit(param.Parameterized):
    # input_image_transform=param.Parameter(doc="Transform to map image np.ndarray to geospatial reference")
    targets_gdf = param.Parameter(default=None, doc="GeoPandas DF of potential targets")
    region_geojson = param.Dict(allow_None=False, doc="Open GeoJSON file defining the work region outline")

    @param.output(
            targets_gdf=param.Parameter,
            removed_targets_gdf=param.Parameter,
    ) # TBD best param type for geoJSON/GDFs
    def output(self):
        return self.map_view.targets_gdf, self.map_view.removed_targets_gdf

    def __init__(self, **params):
        super().__init__(**params)
        self._add_map()
        self._add_download_widgets()

    def _add_map(self):
        targets_points_gdf = self.targets_gdf[['geometry','target_id']] # remove confusing cols
        self.map_view = MapView(
            region_geojson = self.region_geojson,
            targets_gdf = targets_points_gdf
        )

    def _add_download_widgets(self):
        download_targets = DownloadGeoJSON(
            source_gdf=self.map_view.targets_gdf,
            filename="targets.geojson",
            button_type="primary",
            name="Download Targets"
        )
        download_removed_targets = DownloadGeoJSON(
            source_gdf=self.map_view.removed_targets_gdf,
            filename="removed_targets.geojson",
            button_type="warning",
            name="Download Removed Targets"
        )
        self.download_widgets = pn.Column(
            "# Parameterized GeoJSON Downloads",
            pn.Row(
                download_targets.download_widget,
                download_removed_targets.download_widget,
                width=400
            )
        )
        
    def panel(self):
        map_panel = pn.panel(self.map_view.map)
        layout = pn.Column(
            map_panel,
            self.download_widgets
        )
        return layout
    
class StageRouting(param.Parameterized):
    def __init__(self, **params):
        super().__init__(**params)

    @param.output(
    )
    def output(self):
        return

    def panel(self):
        select_row = pn.Row("Find routes to address all targets")
        return select_row