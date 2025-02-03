import param
import panel as pn
import json
import geopandas as gpd
import hashlib
import rasterio
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

from .stage_routing import RoutingMap, RoutingWidgets
from .tesselation import Tesselation

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
        return self.project
    

    def panel(self):
        return pn.Column(
            pn.indicators.BooleanStatus(
                value=self.ready_to_proceed,
                name="Ready to Proceed"
            ),
            self.upload_widgets.view(),  # UI for file uploads
        )
    


class StageSearch(param.Parameterized):
    project = param.ClassSelector(class_=Project, allow_None=False, doc="Pipeline's current project")
    ready_to_proceed = param.Boolean(default=False, doc="Indicates if the stage can proceed")

    def __init__(self, **params):
        super().__init__(**params)

        # Define the Artifact Manager for the Search Stage
        self.artifact_manager = StageArtifactManager(
            project=self.project,
            stage_name="search",
            input_files=[
                "inputs/region_orthophoto.tif" # region image for searching
            ],
            stage_output_dir_name="search",  # Store outputs in `search/`
            output_files=[
                "binary_mask.png", # Store outputs as simple PNG
                "binary_mask.tif" # Store outputs as geo-referenced binary mask
            ],
        )

        # Load inputs as needed
        #   -> If we got here, all inputs are known to exist
        try:
            preloaded_image = self.artifact_manager.get_file_handle("inputs/region_orthophoto.tif")
            if preloaded_image:
                with rasterio.open(preloaded_image) as src:
                    image_array = src.read().transpose(1, 2, 0) # Convert (bands, h, w) to (h, w, bands)
                self.image_array = np.array(image_array) # Needs to be numpy array

        except Exception as e:
                print(f"Error retrieving stage artifacts: {e}")
                raise ValueError("Input artifacts cannot be None in StageSearch initialization")


        # Pre-Load outputs if available
        if self.artifact_manager.has_required_outputs:
            try:
                preloaded_binary_mask = self.artifact_manager.get_file_handle("binary_mask.png")
                if preloaded_binary_mask:
                    with open(preloaded_binary_mask, "rb") as f:
                        binary_mask_bytes = f.read()
                binary_mask = Image.open(BytesIO(binary_mask_bytes)).convert("L")  # Convert to grayscale
                output_mask = np.array(binary_mask)  # Convert to NumPy array (h, w)
                self._add_search_widgets(preloaded_output=output_mask)

            except Exception as e:
                print(f"Error preloading stage files: {e}")
                self._add_search_widgets()

        else:
            self._add_search_widgets()


    @param.output( project=param.ClassSelector(class_=Project) )
    def output(self):

        # Save artifacts using the Artifact Manager
        try:
            search_binary_mask = self.target_search.output_image
            
            # Binary mask as PNG for easy reading
            binary_mask_handle = self.artifact_manager.get_file_handle("binary_mask.png")
            if binary_mask_handle:
                img = Image.fromarray((search_binary_mask).astype("uint8"))  # Scale 0/1 mask to 0-255
                img.save(binary_mask_handle, "PNG")
            
            # Save geo-referenced mask as well
            reference_geotiff_handle = self.artifact_manager.get_file_handle("inputs/region_orthophoto.tif")
            binary_mask_tif_handle = self.artifact_manager.get_file_handle("binary_mask.tif")
            if binary_mask_tif_handle and reference_geotiff_handle:

                # Open the reference GeoTIFF to copy metadata
                with rasterio.open(reference_geotiff_handle) as src:
                    meta = src.meta.copy()  # Copy metadata
                    meta.update({
                        "count": 1,  # Convert to single-band
                        "dtype": search_binary_mask.dtype,  # Use the same dtype as the mask
                    })

                # Save binary mask with the same geospatial properties
                with rasterio.open(binary_mask_tif_handle, "w", **meta) as dst:
                    dst.write(search_binary_mask, 1)  # Write mask to band 1

        except Exception as e:
                print(f"Error saving stage artifacts: {e}")
                return None

        return self.project
    
    def _add_search_widgets(self, preloaded_output=None):
        veg_index = VegetationIndex()
        smoothing = Smoothing()
        contrast = ContrastEnhancement(enabled=False)
        morphological = MorphologicalRefinement(enabled=False)
        thresholding = ManualThresholding()
        
        self.target_search = TargetSearch(
            input_image=self.image_array,
            techniques=[veg_index, smoothing, contrast, morphological, thresholding],
            output_image=preloaded_output
        )

    def panel(self):
        return pn.Column(
            pn.indicators.BooleanStatus(
                value=self.ready_to_proceed,
                name="Ready to Proceed"
            ),
            self.target_search.view
        )
    


class StageAcquireTargets(param.Parameterized):
    project = param.ClassSelector(class_=Project, allow_None=False, doc="Pipeline's current project")
    ready_to_proceed = param.Boolean(default=False, doc="Indicates if the stage can proceed")

    def __init__(self, **params):
        super().__init__(**params)

        # Define the Artifact Manager for the Targeting Stage
        self.artifact_manager = StageArtifactManager(
            project=self.project,
            stage_name="target",
            input_files=[
                "inputs/region_orthophoto.tif", # region image for searching
                "inputs/region_outline.geojson", # OG work region outline
                "search/binary_mask.tif" # Searched region mask
            ],
            stage_output_dir_name="target",  # Store outputs in `target/`
            output_files=[
                "targets.geojson", # Targets as GeoJSON
            ],
        )

        # Load inputs as needed
        #   -> If we got here, all inputs are known to exist
        try:
            preloaded_mask = self.artifact_manager.get_file_handle("search/binary_mask.tif")
            if preloaded_mask:
                with rasterio.open(preloaded_mask) as src:
                    binary_mask = src.read(1) # Should be 2D (w x h) np.ndarray 
                    self.mask_transform = src.transform
                self.binary_mask = np.array(binary_mask) # Needs to be numpy array

        except Exception as e:
                print(f"Error retrieving stage artifacts: {e}")
                raise ValueError("Input artifacts cannot be None in StageSearch initialization")


        # Pre-load stage outputs if available
        #   -> If we pass here, we have run this stage before
        self.targets_gdf = None # Attept to pre-load, if avaiable
        if self.artifact_manager.has_required_outputs:
            try:
                targets_geojson_handle = self.artifact_manager.get_file_handle("targets.geojson")
                if targets_geojson_handle:
                    self.targets_gdf = gpd.read_file(targets_geojson_handle)
            except Exception as e:
                print(f"Error preloading stage files: {e}")


        # Load stage interface widgets
        self.acquire_targets = AcquireTargetsWidget(
            binary_mask=self.binary_mask,
            input_image_transform=self.mask_transform,
            targets_gdf=self.targets_gdf, # Possibly pre-loaded
        )

        self.download_targets = DownloadGeoJSON(
            source_gdf=self.acquire_targets.targets_gdf,
            filename="targets.geojson",
            button_type="primary",
            name="Download Targets"
        )


    @param.output( project=param.ClassSelector(class_=Project) )
    def output(self):
        # Save artifacts using the Artifact Manager
        try:
            found_targets_gdf = self.acquire_targets.targets_gdf
            
            targets_geojson_handle = self.artifact_manager.get_file_handle("targets.geojson")
            if targets_geojson_handle:
                found_targets_gdf.to_file(targets_geojson_handle, driver="GeoJSON")
        except Exception as e:
                print(f"Error saving stage artifacts: {e}")

        return self.project
    

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
    project = param.ClassSelector(class_=Project, allow_None=False, doc="Pipeline's current project")
    ready_to_proceed = param.Boolean(default=False, doc="Indicates if the stage can proceed")

    def __init__(self, **params):
        super().__init__(**params)

        # Define the Artifact Manager for the Audit Stage
        self.artifact_manager = StageArtifactManager(
            project=self.project,
            stage_name="audit",
            input_files=[
                "inputs/region_outline.geojson", # OG work region outline
                "target/targets.geojson" # Auto-discovered targets file
            ],
            stage_output_dir_name="target",  # Store outputs in `target/`
            output_files=[
                "allowed_targets.geojson", # Targets as GeoJSON
                "removed_targets.geojson" # Removed targets as GeoJSON
            ],
        )

        # Load inputs as needed
        #   -> If we got here, all inputs are known to exist
        try:
            region_geojson_handle = self.artifact_manager.get_file_handle("inputs/region_outline.geojson")
            if region_geojson_handle:
                with open(region_geojson_handle, "r") as f:
                    region_outline_geojson = json.load(f)

            targets_geojson_handle = self.artifact_manager.get_file_handle("target/targets.geojson")
            if targets_geojson_handle:
                found_targets_gdf = gpd.read_file(targets_geojson_handle)

        except Exception as e:
                print(f"Error retrieving stage artifacts: {e}")
                raise ValueError("Input artifacts cannot be None in StageSearch initialization")

        # Pre-load stage outputs if available
        #   -> If we pass here, we have run this stage before
        self.targets_gdf = None # Attept to pre-load, if avaiable

        if self.artifact_manager.has_required_outputs:
            try:
                allowed_targets_geojson_handle = self.artifact_manager.get_file_handle("allowed_targets.geojson")
                if allowed_targets_geojson_handle:
                    allowed_targets_gdf = gpd.read_file(allowed_targets_geojson_handle)

                removed_targets_geojson_handle = self.artifact_manager.get_file_handle("removed_targets.geojson")
                if removed_targets_geojson_handle:
                    removed_targets_gdf = gpd.read_file(removed_targets_geojson_handle)
            
                # If we are pre-loading, pass allowed & removed targets to map
                self.map_view = MapView(
                    region_geojson = region_outline_geojson,
                    targets_gdf = allowed_targets_gdf,
                    removed_targets_gdf = removed_targets_gdf
                )

            except Exception as e:
                print(f"Error preloading stage files: {e}")

        else:
            # Initialize with auto-generated targets only
            self.map_view = MapView(
                region_geojson = region_outline_geojson,
                targets_gdf = found_targets_gdf
            )

        # Regardless or pre-load, pass in our download helper widgets
        self._add_download_widgets()

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


    @param.output( project=param.ClassSelector(class_=Project) )
    def output(self):
        allowed_targets = self.map_view.targets_gdf
        removed_targets = self.map_view.removed_targets_gdf

        # Save artifacts using the Artifact Manager
        try:
            allowed_targets_geojson_handle = self.artifact_manager.get_file_handle("allowed_targets.geojson")
            if allowed_targets_geojson_handle and allowed_targets is not None:
                allowed_targets.to_file(allowed_targets_geojson_handle, driver="GeoJSON")

            removed_targets_geojson_handle = self.artifact_manager.get_file_handle("removed_targets.geojson")
            if removed_targets_geojson_handle and removed_targets is not None:
                removed_targets.to_file(removed_targets_geojson_handle, driver="GeoJSON")

        except Exception as e:
                print(f"Error saving stage artifacts: {e}")

        return self.project
        
    def panel(self):
        try:
            # map_panel = pn.pane.IPyLeaflet(self.map_view.map)
            # map_panel = pn.pane.IPyWidget(self.map_view.map)
            map_panel = pn.panel(self.map_view.map) # Seems to be interactive now. Nobody knows why.
            layout = pn.Column(
                map_panel,
                self.download_widgets
            )
            return layout
        except Exception as e:
            print(f"Error displaying stage: {e}")
    



class StageRouting(param.Parameterized):
    project = param.ClassSelector(class_=Project, allow_None=False, doc="Pipeline's current project")
    ready_to_proceed = param.Boolean(default=False, doc="Indicates if the stage can proceed")

    def __init__(self, **params):
        super().__init__(**params)
        
        print("Begin routing stage.")

        # Define the Artifact Manager for the Audit Stage
        self.artifact_manager = StageArtifactManager(
            project=self.project,
            stage_name="routing",
            input_files=[
                "inputs/region_outline.geojson", # OG work region outline
                "target/allowed_targets.geojson" # Audited targets from search
            ],
            stage_output_dir_name="routing",  # Store outputs in `target/`
            output_files=[
                "allowed_targets.geojson", # Targets as GeoJSON
                "removed_targets.geojson" # Removed targets as GeoJSON
            ],
        )
        print("SAM initialized.")

        # Load inputs as needed
        #   -> If we got here, all inputs are known to exist
        try:
            region_geojson_handle = self.artifact_manager.get_file_handle("inputs/region_outline.geojson")
            if region_geojson_handle:
                with open(region_geojson_handle, "r") as f:
                    region_outline_geojson = json.load(f)
                region_outline_gdf = gpd.read_file(region_geojson_handle)

            allowed_targets_geojson_handle = self.artifact_manager.get_file_handle("target/allowed_targets.geojson")
            if allowed_targets_geojson_handle:
                allowed_targets_gdf = gpd.read_file(allowed_targets_geojson_handle)

        except Exception as e:
                print(f"Error retrieving stage artifacts: {e}")
                raise ValueError("Input artifacts cannot be None in StageSearch initialization")


        self.routing_widgets = RoutingWidgets(
            region_geojson=region_outline_geojson,
            region_outline_gdf=region_outline_gdf,
            targets_gdf=allowed_targets_gdf,
        #     cells_gdf=self.tesselation.cells_gdf,
        )
        print("Stage init completed.")

    @param.output( project=param.ClassSelector(class_=Project) )
    def output(self):

        # Save artifacts using the Artifact Manager
        try:
            pass
            # allowed_targets_geojson_handle = self.artifact_manager.get_file_handle("allowed_targets.geojson")
            # if allowed_targets_geojson_handle and allowed_targets is not None:
            #     allowed_targets.to_file(allowed_targets_geojson_handle, driver="GeoJSON")

            # removed_targets_geojson_handle = self.artifact_manager.get_file_handle("removed_targets.geojson")
            # if removed_targets_geojson_handle and removed_targets is not None:
            #     removed_targets.to_file(removed_targets_geojson_handle, driver="GeoJSON")

        except Exception as e:
                print(f"Error saving stage artifacts: {e}")

        return self.project

    def panel(self):
            
        return pn.Column(
            pn.indicators.BooleanStatus(
                value=self.ready_to_proceed,
                name="Ready to Proceed"
            ),
            self.routing_widgets.view()
        )
    


class StageDownload(param.Parameterized):
    project = param.ClassSelector(class_=Project, allow_None=False, doc="Pipeline's current project")
    ready_to_proceed = param.Boolean(default=False, doc="Indicates if the stage can proceed")

    def __init__(self, **params):
        super().__init__(**params)
        
        # Define the Artifact Manager for the Audit Stage
        self.artifact_manager = StageArtifactManager(
            project=self.project,
            stage_name="routing",
            input_files=[
                "inputs/region_outline.geojson", # OG work region outline
                "target/allowed_targets.geojson" # Audited targets from search
            ],
            stage_output_dir_name="routing",  # Store outputs in `target/`
            output_files=[
                "allowed_targets.geojson", # Targets as GeoJSON
                "removed_targets.geojson" # Removed targets as GeoJSON
            ],
        )


    @param.output( project=param.ClassSelector(class_=Project) )
    def output(self):
        return self.project

    def panel(self):
        select_row = pn.Row("Download all project artifacts")
        return select_row