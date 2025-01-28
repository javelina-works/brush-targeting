import panel as pn
import param
import geopandas as gpd
from io import BytesIO

class DownloadGeoJSON(param.Parameterized):
    # Parameter to hold the GeoDataFrame
    source_gdf = param.ClassSelector(class_=gpd.GeoDataFrame, default=None, allow_None=True)
    filename = param.String(default="output.geojson")
    button_type = param.String(default="primary")
    name = param.String(default="Download")

    def get_geojson_file(self):
        """
        Convert the current GeoDataFrame (source_gdf) to a GeoJSON string for download.
        """
        if self.source_gdf is None:
            print("Download GeoJSON: No GeoDataFrame is set!")
            return BytesIO()  # Return an empty file
        bio = BytesIO()
        self.source_gdf.to_file(bio, driver="GeoJSON")
        bio.seek(0)
        return bio

    @param.depends("source_gdf", "filename", "button_type", "name")
    def download_widget(self):
        """
        Return a FileDownload widget based on the current state of the parameters.
        """
        return pn.widgets.FileDownload(
            callback=lambda: self.get_geojson_file(),
            filename=self.filename,
            button_type=self.button_type,
            name=self.name
        )