import param
import panel as pn
import geopandas as gpd
from io import BytesIO
import json
import geoviews as gv
from PIL import Image
import rasterio

# gv.extension('bokeh')
pn.extension('filedropper')

from bokeh.model import Model
# import logging

# logging.basicConfig(level=logging.DEBUG)

def log_bokeh_model_ids(obj, name=""):
    """Logs IDs of Bokeh models for debugging."""
    if isinstance(obj, Model):
        print(f"Bokeh Model {name}: {obj}, ID={obj.id}")
    elif isinstance(obj, (list, tuple)):
        for i, o in enumerate(obj):
            log_bokeh_model_ids(o, f"{name}[{i}]")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            log_bokeh_model_ids(v, f"{name}[{k}]")
    else:
        print(f"Non-Bokeh object {name}: {obj}")


class UploadRegionFiles(param.Parameterized):
    # Parameters for tracking uploaded files
    region_image_upload = param.Parameter(default=None, doc="Uploaded orthophoto geotif of work region")
    region_geojson_upload = param.Parameter(default=None, doc="Uploaded geoJSON of work region outline")
    region_image_thumbnail_dims = param.Integer(default=1000, step=250, bounds=(250, 2000), doc="Max dims of uploaded image thumbnail")

    region_image_upload_name = param.Parameter(default=None)
    region_geojson_upload_name = param.Parameter(default=None)

    # FileDropper widgets

    # Accepted filetypes bug for this widget: https://github.com/holoviz/panel/issues/7153
    # accepted_filetypes=["allowed/geojson", ".geojson"],
    # Unable to handle our large geoTiff images
    image_dropper = pn.widgets.FileDropper(height=100, max_file_size ="500MB", chunk_size=10_000_000)
    geojson_dropper = pn.widgets.FileDropper(height=100, max_file_size ="100MB")

    def __init__(self, **params):
        super().__init__(**params)

        # Link FileDropper outputs to parameters
        self.image_dropper.param.watch(self._update_region_image, "value")
        self.geojson_dropper.param.watch(self._update_region_geojson, "value")

    # Update methods for parameters
    def _update_region_image(self, event):
            # Upate for all events, including removal of file
            self.region_image_upload = event.new
            self.get_region_image() # Update name & contents when possible

    def _update_region_geojson(self, event):
        self.region_geojson_upload = event.new
        self.get_region_geojson() # Update name & contents when event triggered

    def get_region_geotiff(self):
        if self.region_image_upload:
            image_upload_dict = self.region_image_upload # Stays as dict of files
            first_file_name = list(image_upload_dict.keys())[0] # Dict of file names:bytes
            image_stream  = BytesIO(image_upload_dict[first_file_name]) # Bytes to Stream

            # region_image = Image.open(image_stream)  # Stream to PIL image
            with rasterio.open(image_stream) as src:
                region_image = {
                    "data": src.read().transpose(1, 2, 0), # Convert (bands, h, w) to (h, w, bands)
                    "crs": src.crs,      # Coordinate Reference System
                    "transform": src.transform  # Affine transform
                }
            return region_image
        else:
            return None

    def get_region_image(self):
        if self.region_image_upload:
            image_upload_dict = self.region_image_upload # Stays as dict of files
            first_file_name = list(image_upload_dict.keys())[0] # Dict of file names:bytes
            image_stream  = BytesIO(image_upload_dict[first_file_name]) # Bytes to Stream
            region_image = Image.open(image_stream)  # Stream to PIL image

            self.region_image_upload_name = first_file_name
            return region_image
        else:
            self.region_image_upload_name = None
            return None

    def get_region_geojson(self):
        if self.region_geojson_upload:
            geojson_upload_dict = self.region_geojson_upload # Dict of files
            first_file_name = list(geojson_upload_dict.keys())[0] # Dict of file names:bytes
            file_bytes_string = geojson_upload_dict[first_file_name].decode("utf-8") # Bytes to string
            region_geojson = json.loads(file_bytes_string)  # String to JSON dict
            
            self.region_geojson_upload_name = first_file_name
            return region_geojson
        else:
            self.region_geojson_upload_name = None # Remember to reset when deleted
            return None

    def view_image(self):
        if self.region_image_upload:
            try:
                pil_image = self.get_region_image()
                thumb_dim = self.region_image_thumbnail_dims
                pil_image.thumbnail((thumb_dim, thumb_dim))
                return pn.pane.Image(pil_image, height=500, width=500)
            except Exception as e:
                return f"Error displaying image: {e}"
        else:
            return "No image uploaded."

    # A method to display the GeoJSON region outline
    def view_geojson(self):
        if self.region_geojson_upload:
            try:
                region_geojson = self.get_region_geojson()
                
                json_pane = pn.pane.JSON(region_geojson, depth=2, name="Uploaded GeoJSON")

                gdf = gpd.GeoDataFrame.from_features(region_geojson["features"])
                # gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.001)  # Reduce geometry complexity
                gv_geojson = gv.Polygons(gdf, vdims=["name"] if "name" in gdf.columns else None).opts(
                    fill_alpha=0.5,
                    line_width=2,
                    color="blue",
                    tools=["hover"],
                    active_tools=["wheel_zoom"],
                    width=600,
                    height=400,
                    title="Region Outline Visualization"
                )
                # view_pane = pn.pane.HoloViews(gv_geojson, height=400, width=600)

                geojson_row = pn.Row( 
                    json_pane, 
                    pn.pane.HoloViews(gv_geojson, height=400, width=600)
                )
                return geojson_row
            except Exception as e:
                return f"Error processing GeoJSON: {e}"
        else:
            return "No GeoJSON uploaded."

    # Panel layout combining file droppers and visualizations
    def view(self):
        return pn.Column(
            pn.Row(
                pn.Column("**Drop Region Image Here**", self.image_dropper),
                pn.Column("**Drop GeoJSON Here**", self.geojson_dropper),
            ),
            pn.Row(
                pn.Column("**Uploaded Region Image**", self.view_image),
                pn.Column("**Uploaded GeoJSON Outline**", self.view_geojson)
            ),
        )

# # Run the app
# target_audit_app = UploadRegionFiles()
# target_audit_app.view().servable()

# target_audit_app.view().show()