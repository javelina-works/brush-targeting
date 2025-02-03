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


class RoutingMap(param.Parameterized):
    # region_image_path = param.String(doc="Path to the orthophoto image")
    region_geojson = param.Dict(allow_None=False, doc="Open GeoJSON file defining the work region outline")
    targets_gdf = param.Parameter(default=None, doc="GeoPandas DF of potential targets")

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
        self._add_targets_layer()
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

    def _add_map_controls(self):
        # self.map.add(ZoomControl(position='bottomleft'))
        self.map.add(FullScreenControl(position="topleft"))
        self.map.add(LayersControl(position="topright"))
        self.map.add(ScaleControl(position="bottomleft"))

    def _add_draw_control(self):
        self.draw_control = GeomanDrawControl(
            circlemarker = {},
            polygon = {},
            polyline = {},
            rectangle = {"pathOptions": {"weight": 2, "color": "green", "fillOpacity": 0.1}},

            rotate = False,
            cut = False,
            edit = False,
            drag = False, # Does not maintain state 
            remove = False, # Swap GDFs, don't remove
        )
        self.map.add(self.draw_control)

    



