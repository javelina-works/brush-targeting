import panel as pn
import param
import geopandas as gpd
import json

from brush_targeting.macro_planning.depot_placement import find_depots


class DepotPlacement(param.Parameterized):
    depot_radius = param.Number(default=225, step=5, doc="Serviceable range of depot in meters")
    grid_density = param.Number(default=4, bounds=(1,20), doc="Density of generated candidate points in target region")

    cells_gdf = param.ClassSelector(class_=gpd.GeoDataFrame, default=None, allow_None=True, doc="Region cells to be covered")
    region_outline_gdf = param.ClassSelector(class_=gpd.GeoDataFrame, default=None, allow_None=True, doc="Work region outline")
    
    depots_gdf = param.ClassSelector(class_=gpd.GeoDataFrame, default=None, allow_None=True, doc="Discovered depot locations.")

    # Define CRS
    processing_crs = "EPSG:32613"  # UTM Zone (example: adjust based on region)
    display_crs = "EPSG:4326"  # For leaflet visualization

    def __init__(self, **params):
        super().__init__(**params)

    def _click_find_depots(self, event):
        if self.cells_gdf is not None and self.region_outline_gdf is not None:
            passed_crs = self.region_outline_gdf.crs
            cells_projected = self.cells_gdf.to_crs(self.processing_crs) # Convert to projected CRS for accurate calculations
            region_projected = self.region_outline_gdf.to_crs(self.processing_crs) # Convert to projected CRS for accurate calculations

            depots_projected = self.find_depots(cells_projected, region_projected)
            self.depots_gdf = depots_projected.to_crs(passed_crs)
        else:
            print("No valid cells or region provided")


    def find_depots(self, cells_gdf, region_gdf):
        if cells_gdf is not None and region_gdf is not None:
            return find_depots(self.depot_radius, cells_gdf, region_gdf, self.grid_density)
        else:
            print("Cells and region outline must both be defined")

    
    def view(self):
        return pn.Column(
            self.param.depot_radius,
            self.param.grid_density,
            pn.widgets.Button(name="Find Depots", button_type="primary", on_click=self._click_find_depots)
        )