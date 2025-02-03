import panel as pn
import param
import geopandas as gpd
import json

from brush_targeting.plant_search.region_partition import centroidal_voronoi_tessellation


class Tesselation(param.Parameterized):
    target_area_acres = param.Number(default=0.5, doc="How large in acres each cell should approximately be.")
    max_iterations = param.Integer(default=15, doc="Number of iterations to determine tesselation for work region")
    region_outline_gdf = param.ClassSelector(class_=gpd.GeoDataFrame, doc="Region to tesselate into cells")
    cells_gdf = param.ClassSelector(class_=gpd.GeoDataFrame, default=None, allow_None=True, doc="Region tesselated into cells")
    cells_geojson = param.Dict(default=None, doc="GeoJSON of the region partitioning.")

    # Define CRS
    processing_crs = "EPSG:32613"  # UTM Zone (example: adjust based on region)
    display_crs = "EPSG:4326"  # For leaflet visualization

    def __init__(self, **params):
        super().__init__(**params)
        self._update_cell_params()

    @param.depends('target_area_acres', watch=True)
    def _update_cell_params(self):
        self.target_area_sqm = self.target_area_acres * 4046.86 # Track area in sq. m


    def perform_tesselation(self, event):
        """Run tessellation and update cells_gdf."""
        if self.region_outline_gdf is not None and not self.region_outline_gdf.empty:
            
            self.cells_gdf = self.tesselate_region(self.region_outline_gdf)
            self.cells_gdf.to_crs(self.display_crs, inplace=True)
            
            geojson_str = self.cells_gdf.drop(columns=["cell_centroid"]).to_json() # Convert to JSON string
            geojson_dict = json.loads(geojson_str) # Convert JSON string to dictionary
            geojson_dict["crs"] = {"type": "name", "properties": {"name": self.cells_gdf.crs.to_string()}} # Embed CRS information
            self.cells_geojson = geojson_dict
            
            print("Tessellation completed.")  # Debugging log
        else:
            print("No valid region_outline_gdf provided.")


    def tesselate_region(self, region_gdf: gpd.GeoDataFrame):
        if region_gdf is not None and not region_gdf.empty:
            passed_crs = region_gdf.crs
            region_projected = self.region_outline_gdf.to_crs(self.processing_crs) # Convert to projected CRS for accurate calculations
            
            region_polygon = region_projected.geometry.iloc[0]
            num_cells = int(region_polygon.area / self.target_area_sqm) # How many cells to generate

            tessellated_gdf = centroidal_voronoi_tessellation(region_polygon, num_cells, self.max_iterations)
            cells_gdf = tessellated_gdf.to_crs(passed_crs) # revert back to passed crs
            return cells_gdf



    def view(self):
        return pn.Column(
            self.param.target_area_acres,
            self.param.max_iterations,
            pn.widgets.Button(name="Tesselate", button_type="primary", on_click=self.perform_tesselation),
            pn.pane.JSON(self.cells_geojson, depth=2, name="Voronoi cells")
        )
