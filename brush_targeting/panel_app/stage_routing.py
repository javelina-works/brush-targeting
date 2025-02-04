from ipyleaflet import (
    Map, GeoJSON, TileLayer, GeoData, 
    WidgetControl, LayersControl, ScaleControl, 
    GeomanDrawControl, FullScreenControl, ZoomControl
)
from panel.widgets import Button
import ipywidgets
import param
import panel as pn
import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import shape

from .tesselation import Tesselation
from .depot_placement import DepotPlacement

class RoutingMap(param.Parameterized):
    # region_image_path = param.String(doc="Path to the orthophoto image")
    region_geojson = param.Dict(allow_None=False, doc="Open GeoJSON file defining the work region outline")
    targets_gdf = param.Parameter(default=None, doc="GeoPandas DF of potential targets")

    cells_gdf = param.Parameter(default=None, doc="GeoPandas DF of region Voronoi")
    voronoi_data = param.Dict(default=None, doc="GeoJSON of region voronoi")
    depots_data = param.Dict(default=None, doc="GeoJSON of depots")


    def __init__(self, **params):
        super().__init__(**params)
        self.map = None
        self.region_data = None

        self._initialize_region_data()
        self._initialize_map()

    def _initialize_region_data(self):
        self.region_data = self.region_geojson
        region_geometry = shape(self.region_data['features'][0]['geometry'])
        self.region_center = region_geometry.centroid

    def _initialize_map(self):
        self.map = Map(center=(self.region_center.y, self.region_center.x), zoom=16, scroll_wheel_zoom=True)

        # self.tile_layer = TileLayer(
        #     url="http://localhost:8000/{z}/{x}/{y}.png",
        #     min_zoom=15, max_zoom=22,
        #     name="Region Image"
        # )
        # self.map.add(self.tile_layer)

        self._add_region_outline_layer()
        # self._add_targets_layer()
        self._add_cells_layer()
        self._add_depots_layer()
        self._add_map_controls()
        self._add_draw_control()


    def _add_region_outline_layer(self):
        region_layer = GeoJSON(
            data=self.region_data, 
            style={'color': 'blue', 'fillOpacity': 0.05, 'weight': 2},
            name=self.region_data['name'])
        self.map.add(region_layer) # Add the region border to the map

    def _add_targets_layer(self):
        self.targets_layer = GeoData(
            geo_dataframe=self.targets_gdf,
            style={'color': 'black', 'radius':6, 'fillColor': 'blue', 'opacity':0.5, 'weight':1, 'fillOpacity':0.3},
            hover_style={'fillColor': 'blue' , 'fillOpacity': 0.2},
            point_style={'radius': 3, 'color': 'red', 'fillOpacity': 0.8, 'fillColor': 'blue', 'weight': 3},
            draggable=True,
            name="Identified targets"
            )
        self.map.add(self.targets_layer)

    @param.depends('voronoi_data', watch=True)
    def _update_cells_layer(self):
        if self.voronoi_layer is not None:
            self.map.remove(self.voronoi_layer) # Prevent stacking multiple layers
        self._add_cells_layer() # Refresh layer, regardless of data


    def _add_cells_layer(self):
        if self.voronoi_data is None:
            self.voronoi_layer = None # Start with none, update as needed
            return # Skip this layer

        self.voronoi_layer = GeoJSON(
            data=self.voronoi_data, 
            style={'color': 'blue', 'fillColor': 'lightblue', 'opacity': 0.25, 'weight': 1},
            name="Region cells")
            # name=self.voronoi_data['name'])
        self.map.add(self.voronoi_layer)


    @param.depends('depots_data', watch=True)
    def _update_depots_layer(self):
        if self.depot_layer is not None:
            self.map.remove(self.depot_layer) # Prevent stacking multiple layers
        self._add_depots_layer() # Refresh layer, regardless of data


    def _add_depots_layer(self):
        if self.depots_data is None:
            self.depot_layer = None # Start with none, update as needed
            return # Skip this layer

        depot_radius = self.depots_data['features'][0]['properties']['depot_radius']

        self.depot_layer = GeoJSON(
            data=self.depots_data, 
            style={'color': 'black', 'radius':6, 'fillColor': 'blue', 'opacity':0.9, 'weight':1, 'fillOpacity':0.3},
            hover_style={'fillColor': 'red', 'fillOpacity': 0.2},
            point_style={'radius': 5, 'color': 'red', 'fillOpacity': 0.8, 'fillColor': 'blue', 'weight': 3},
            draggable=True,
            name="Depot locations")
        self.map.add(self.depot_layer)

    def _add_map_controls(self):
        # self.map.add(ZoomControl(position='bottomleft'))
        self.map.add(FullScreenControl(position="topleft"))
        self.map.add(LayersControl(position="topright"))
        self.map.add(ScaleControl(position="bottomleft"))

    def _add_draw_control(self):
        self.draw_control = GeomanDrawControl(
            circlemarker = {"pathOptions": {"weight": 2, "color": "green", "fillOpacity": 0.1}},
            polygon = {},
            polyline = {},
            rectangle = {},

            rotate = False,
            cut = False,
            edit = False,
            drag = True, # Does not maintain state 
            remove = False, # Swap GDFs, don't remove
        )
        self.map.add(self.draw_control)




class RoutingWidgets(param.Parameterized):
    region_geojson = param.Dict(allow_None=False, doc="Open GeoJSON file defining the work region outline")
    region_outline_gdf = param.ClassSelector(class_=gpd.GeoDataFrame, doc="Region to tesselate into cells")
    targets_gdf = param.Parameter(default=None, doc="GeoPandas DF of potential targets")

    cells_gdf = param.Parameter(default=None, doc="GeoPandas DF of region Voronoi")
    tesselation = param.ClassSelector(class_=Tesselation, default=None, doc="Handles functions maintaining cell tesselation")
    find_depots = param.ClassSelector(class_=DepotPlacement, default=None, doc="Finds optimal depot placements")
    routing_map = param.ClassSelector(class_=RoutingMap, doc="Displays the map for determining routes")

    def __init__(self, **params):
        super().__init__(**params)

        self.routing_map = RoutingMap(
            region_geojson=self.region_geojson,
            targets_gdf=self.targets_gdf,
            # cells_gdf=self.tesselation.cells_gdf,
        )

        # Must init before Tesselation or callback will cause error
        self.find_depots = DepotPlacement(
            cells_gdf=None,
            region_outline_gdf=self.region_outline_gdf
        )
        self.tesselation = Tesselation(
            region_outline_gdf=self.region_outline_gdf
        )
        print("Routing widgets init.")

    
    @param.depends('tesselation.cells_gdf', watch=True)
    def _update_cells_gdf(self):
        self.find_depots.cells_gdf = self.tesselation.cells_gdf

    @param.depends('tesselation.cells_geojson', watch=True)
    def _update_voronoi_cells(self):
        # self.routing_map.param.update(cells_gdf=self.tesselation.cells_gdf)
        self.routing_map.voronoi_data=self.tesselation.cells_geojson
        # print(self.routing_map.voronoi_data)

    @param.depends('find_depots.depots_gdf', watch=True)
    def _update_depot_placements(self):
        if self.find_depots.depots_gdf is not None:
            depots_data = json.loads(self.find_depots.depots_gdf.to_json())
            self.routing_map.depots_data = depots_data

    def view(self):
        try:
            # map_panel = pn.pane.IPyLeaflet(self.map_view.map)
            # map_panel = pn.pane.IPyWidget(self.map_view.map)
            map_panel = pn.panel(self.routing_map.map) # Seems to be interactive now. Nobody knows why.
            layout = pn.Row(
                pn.Column(
                    pn.Card(self.tesselation.view(), title="Region Tesselation"),
                    pn.Card(self.find_depots.view(), title="Depot Placement"),
                ),
                map_panel,
            ) 
            return layout
        except Exception as e:
            print(f"Error displaying stage: {e}")



    



