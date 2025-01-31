import param
import panel as pn
import geopandas as gpd
from io import BytesIO
import json
import geoviews as gv
from PIL import Image
import rasterio

gv.extension('bokeh')
pn.extension('filedropper')



class UploadRegionFiles(param.Parameterized):
    # Parameters for tracking uploaded files
    region_image_bytes = param.ClassSelector(class_=BytesIO, default=None, doc="Uploaded orthophoto geotif of work region")
    region_geojson_dict = param.Dict(default=None, doc="Dict of uploaded geoJSON of work region outline")
    region_image_thumbnail_dims = param.Integer(default=1000, step=250, bounds=(250, 2000), doc="Max dims of uploaded image thumbnail")

    # Accepted filetypes bug for this widget: https://github.com/holoviz/panel/issues/7153
    # accepted_filetypes=["allowed/geojson", ".geojson"],
    # Unable to handle our large geoTiff images
    image_dropper = pn.widgets.FileDropper(height=100, max_file_size ="500MB", chunk_size=10_000_000)
    geojson_dropper = pn.widgets.FileDropper(height=100, max_file_size ="100MB")

    def __init__(self, **params):
        super().__init__(**params)
        self.image_dropper.param.watch(self._update_region_image, "value")
        self.geojson_dropper.param.watch(self._update_region_geojson, "value")

    def _update_region_image(self, event):
        if event.new: # only on new events
            try:
                image_upload_dict = event.new # Stays as dict of files
                first_file_name = list(image_upload_dict.keys())[0] # Dict of file names:bytes
                image_stream  = BytesIO(image_upload_dict[first_file_name]) # Bytes to Stream
                # image_stream.seek(0)
                self.region_image_bytes = image_stream
            except Exception as e:
                print(f"Error retrieving GeoTIFF: {e}")
                self.region_image_bytes = None

    def _update_region_geojson(self, event):
        if event.new:
            try:
                geojson_upload_dict = event.new # Dict of files
                first_file_name = list(geojson_upload_dict.keys())[0] # Dict of file names:bytes
                file_bytes_string = geojson_upload_dict[first_file_name] # Bytes to string
                file_bytes_string = geojson_upload_dict[first_file_name].decode("utf-8") # Bytes to string
                self.region_geojson_dict = json.loads(file_bytes_string)  # String to JSON dict
            except Exception as e:
                print(f"Error retrieving GeoJSON: {e}")
                self.region_geojson_dict = None

    def view_image(self):
        if self.region_image_bytes:
            try:
                # self.region_image_bytes.seek(0)
                pil_image = Image.open(self.region_image_bytes)  # Stream to PIL image
                thumb_dim = self.region_image_thumbnail_dims
                pil_image.thumbnail((thumb_dim, thumb_dim))
                return pn.pane.Image(pil_image, height=500, width=500)
            except Exception as e:
                return f"Error displaying image: {e}"
        else:
            return "No image uploaded."

    def view_geojson(self):
        if self.region_geojson_dict:
            try:
                gdf = gpd.GeoDataFrame.from_features(self.region_geojson_dict["features"])
                gv_geojson = gv.Polygons(gdf, vdims=["name"] if "name" in gdf.columns else None).opts(
                    fill_alpha=0.5, line_width=2, color="blue",
                    tools=["hover"], active_tools=["wheel_zoom"],
                    width=600, height=400,
                    title="Region Outline Visualization"
                )
                return pn.Row( 
                    pn.pane.JSON(self.region_geojson_dict, depth=2, name="Uploaded GeoJSON"), 
                    pn.pane.HoloViews(gv_geojson, height=400, width=600)
                )
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
