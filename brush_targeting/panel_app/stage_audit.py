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

class MapView(param.Parameterized):
    # region_image_path = param.String(doc="Path to the orthophoto image")
    region_geojson = param.Dict(allow_None=False, doc="Open GeoJSON file defining the work region outline")
    targets_gdf = param.ClassSelector(class_=gpd.GeoDataFrame, doc="GeoPandas DF of potential targets")
    removed_targets_gdf = param.ClassSelector(class_=gpd.GeoDataFrame, default=None, allow_None=True, doc="GeoPandas DF of potential targets")

    # map = param.ClassSelector(class_=Map, default=None, doc="Map of our audited targets")
    # targets_layer = param.Parameter(default=None, doc="Targets layer")
    # removed_targets_layer = param.Parameter(default=None, doc="Removed targets layer")

    def param_watcher(self, *events):
        for event in events:
            print(f"Parameter '{event.name}' changed from {event.old} to {event.new}")


    def __init__(self, **params):
        super().__init__(**params)

        try:
            # pn.extension('ipywidgets')
            # self.param.watch(self.param_watcher, list(self.param))

            self.map = None
            # self.removed_targets_gdf = gpd.GeoDataFrame(columns=self.targets_gdf.columns, geometry='geometry')

            if self.targets_gdf is None:
                self.targets_gdf = gpd.GeoDataFrame(columns=['target_id', 'geometry'], geometry='geometry')
            
            if self.removed_targets_gdf is None: # Copy form of input if not pre-loading
                self.removed_targets_gdf = gpd.GeoDataFrame(columns=self.targets_gdf.columns, geometry='geometry')
            
            # self.sample_boxes_gdf = None
            # self.combined_gdf = None
            self.drawn_rectangles = []
            self.region_data = None
            self._initialize_region_data()
            self._initialize_map()
        except Exception as e:
            print(f"Error initializing MapView: {e}")

        import time
        time.sleep(1)
        

    def _initialize_region_data(self):
        self.region_data = self.region_geojson
        region_geometry = shape(self.region_data['features'][0]['geometry'])
        self.region_center = region_geometry.centroid

    def _initialize_map(self):
        self.map = Map(center=(self.region_center.y, self.region_center.x), zoom=16, scroll_wheel_zoom=True)
        # self.map.param.trigger('layers')  # Force refresh

        # self.tile_layer = TileLayer(
        #     url="http://localhost:8000/{z}/{x}/{y}.png",
        #     min_zoom=15, max_zoom=22,
        #     name="Region Image"
        # )
        # self.map.add(self.tile_layer)

        self._add_region_outline_layer()
        self._add_targets_layer()
        self._add_removed_targets_layer()
        self._add_map_controls()
        self._add_draw_control()
        self._add_mass_remove_button()

        # self.map.on_interaction(self._on_map_click)

    def _on_map_click(self, event, **kwargs):
        # Ensure it's a 'click' event (ignore 'mousemove', 'preclick', etc.)
        if kwargs.get("type") != "click": return  

        coordinates = kwargs.get("coordinates")
        if not coordinates: return  # Exit if no coordinates are provided

        lat, lon = coordinates

        new_target = gpd.GeoDataFrame(
            [{'target_id': f'new_{len(self.targets_gdf)}', 'geometry': None}],  # Placeholder geometry
            columns=['target_id', 'geometry']
        )

        new_target["geometry"] = gpd.points_from_xy([lon], [lat]) # Explicitly convert to Shapely geometry
        new_target.set_geometry("geometry", inplace=True) # Assign CRS only after confirming the geometry column exists

        if self.targets_gdf.crs:
            new_target.set_crs(self.targets_gdf.crs, inplace=True)

        # Append the new point to the targets DataFrame
        self.targets_gdf = pd.concat([self.targets_gdf, new_target], ignore_index=True)

        # Update the map layer to show the new point
        # self.targets_layer.geo_dataframe = self.targets_gdf
        self.map.remove_layer(self.targets_layer)
        self.targets_layer.geo_dataframe = self.targets_gdf
        self.map.add(self.targets_layer)
        print(f"Added new target at {lat}, {lon}")


    def _add_region_outline_layer(self):
        region_layer = GeoJSON(
            data=self.region_data, 
            style={'color': 'blue', 'fillOpacity': 0.05, 'weight': 2},
            name=self.region_data['name'])
        self.map.add(region_layer) # Add the region border to the map

    # @param.depends('targets_gdf', watch=True)
    # def _update_targets_layer(self):
    #     self.targets_layer.geo_dataframe = self.targets_gdf

    # @param.depends('removed_targets_gdf', watch=True)
    # def _update_removed_targets_layer(self):
    #     self.removed_targets_layer.geo_dataframe = self.removed_targets_gdf

    # @param.depends('targets_gdf', 'removed_targets_gdf', watch=True)
    # def _update_layers(self):
    #     with param.parameterized.batch_call_watchers(self):
    #         self.targets_layer.geo_dataframe = self.targets_gdf
    #         self.removed_targets_layer.geo_dataframe = self.removed_targets_gdf

    def _add_targets_layer(self):
        self.targets_layer = GeoData(
            geo_dataframe=self.targets_gdf,
            style={'color': 'black', 'radius':6, 'fillColor': 'blue', 'opacity':0.5, 'weight':1, 'fillOpacity':0.3},
            hover_style={'fillColor': 'blue' , 'fillOpacity': 0.2},
            point_style={'radius': 3, 'color': 'red', 'fillOpacity': 0.8, 'fillColor': 'blue', 'weight': 3},
            name="Identified targets"
            )
        
        def on_click_target(event, feature, properties, id):
            # Move the clicked point to the removed targets layer
            target_id = properties['target_id']
            clicked_point = self.targets_gdf[self.targets_gdf['target_id'] == target_id]
            print(f"Clicked a target: {target_id}")
            print(f"GDF Lengths: t{len(self.targets_gdf)}, r{len(self.removed_targets_gdf)}")

            # Remove from targets_gdf
            self.targets_gdf = self.targets_gdf[self.targets_gdf['target_id'] != target_id]
            self.targets_layer.geo_dataframe = self.targets_gdf

            # Add to removed_targets_gdf
            self.removed_targets_gdf = pd.concat([self.removed_targets_gdf, clicked_point])
            self.removed_targets_layer.geo_dataframe = self.removed_targets_gdf
            print(f"GDF Lengths: t{len(self.targets_gdf)}, r{len(self.removed_targets_gdf)}")
            
            # new_targets_gdf = self.targets_gdf[self.targets_gdf['target_id'] != target_id]
            # new_removed_targets_gdf = pd.concat([self.removed_targets_gdf, clicked_point])

            # self.targets_layer.geo_dataframe = new_targets_gdf
            # self.removed_targets_layer.geo_dataframe = new_removed_targets_gdf

            # with param.parameterized.batch_call_watchers(self):
            #     self.targets_gdf = new_targets_gdf
            #     self.removed_targets_gdf = new_removed_targets_gdf

        self.targets_layer.on_click(on_click_target)
        self.map.add(self.targets_layer)

    def _add_removed_targets_layer(self):
        self.removed_targets_layer = GeoData(
            geo_dataframe=self.removed_targets_gdf,
            style={'color': 'black', 'radius':6, 'fillColor': 'red', 'opacity':0.5, 'weight':1, 'fillOpacity':0.3},
            hover_style={'fillColor': 'red' , 'fillOpacity': 0.2},
            point_style={'radius': 3, 'color': 'red', 'fillOpacity': 0.8, 'fillColor': 'blue', 'weight': 3},
            name="Removed targets"
            )
        
        def on_click_removed_target(event, feature, properties, id):
            print("Clicked a removed target")
            target_id = properties['target_id']
            clicked_point = self.removed_targets_gdf[self.removed_targets_gdf['target_id'] == target_id]

            self.removed_targets_gdf = self.removed_targets_gdf[self.removed_targets_gdf['target_id'] != target_id]
            self.removed_targets_layer.geo_dataframe = self.removed_targets_gdf # Remove from removed_targets_gdf
            
            self.targets_gdf = pd.concat([self.targets_gdf, clicked_point]) # Add back to targets_gdf
            self.targets_layer.geo_dataframe = self.targets_gdf

        self.removed_targets_layer.on_click(on_click_removed_target)
        self.map.add(self.removed_targets_layer)

    def _add_draw_control(self):
        # self.draw_control = GeomanDrawControl(
        #     circlemarker = {},
        #     polygon = {},
        #     polyline = {},
        #     rectangle = {"pathOptions": {"weight": 2, "color": "green", "fillOpacity": 0.1}},

        #     rotate = False,
        #     cut = False,
        #     edit = False,
        #     drag = False, # Does not maintain state 
        #     remove = False, # Swap GDFs, don't remove
        # )

        self.draw_control = GeomanDrawControl()
        
        self.draw_control.circlemarker = {}
        self.draw_control.polygon = {}
        self.draw_control.polyline = {}
        self.draw_control.rectangle = {"pathOptions": {"weight": 2, "color": "green", "fillOpacity": 0.1}}
        
        self.draw_control.rotate = False
        self.draw_control.cut = False
        self.draw_control.edit = False
        self.draw_control.drag = False # Does not maintain state 
        self.draw_control.remove = False # Swap GDFs, don't remove

        self.map.add(self.draw_control)


    def _add_map_controls(self):
        # self.map.add(ZoomControl(position='bottomleft'))
        self.map.add(FullScreenControl(position="topleft"))
        self.map.add(LayersControl(position="topright"))
        self.map.add(ScaleControl(position="bottomleft"))

    def _add_mass_remove_button(self):
        self.button = ipywidgets.Button(
            description="Process Rectangles", 
            tooltip="Remove all targets in selections",  # Tooltip text
            icon="rectangle-xmark"
        )

        def process_rectangles(event):
            if not self.draw_control.data or not isinstance(self.draw_control.data, list):
                print("no drawn")
                return # No drawn geometries
            drawn_geometries = [
                shape(item["geometry"])
                for item in self.draw_control.data # Extract valid geometries from draw control data
                if "geometry" in item
            ]
            if not drawn_geometries:
                print("no valid drawn")
                return # Exit early if no valid geometries are found
            
            all_selections = gpd.GeoSeries(drawn_geometries).union_all() # Combine selections
            points_in_selections = self.targets_gdf[self.targets_gdf.geometry.within(all_selections)]
            if points_in_selections.empty:
                return # No points found within the drawn rectangles

            self.removed_targets_gdf = pd.concat([self.removed_targets_gdf, points_in_selections])
            self.targets_gdf = self.targets_gdf[~self.targets_gdf.index.isin(points_in_selections.index)]

            self.targets_layer.geo_dataframe = self.targets_gdf # Update the layers
            self.removed_targets_layer.geo_dataframe = self.removed_targets_gdf
            self.draw_control.clear() # Clear the drawn rectangles
    
        self.button.on_click(process_rectangles)
        self.map.add(WidgetControl(widget=self.button, position='bottomright'))

    # @param.depends('targets_layer', 'removed_targets_layer', watch=False)
    def _view_map(self):
        print("triggering map re-render")

        # map_panel = self.map
        # map_panel = pn.panel(self.map)
        map_panel = pn.panel(self.param.map)
        # self._map_panel = pn.pane.IPyWidget(self.map, width=800, height=600)
        return map_panel

    def view(self):
        print("Triggering audit view.")
        map_section = self._view_map
        audit_panel = pn.Column(
            # self._view_map,
            map_section,
        )
        return audit_panel
        # return audit_panel.servable()