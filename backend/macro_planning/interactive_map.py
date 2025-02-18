from ipyleaflet import (
    Map, GeoJSON, WidgetControl, FullScreenControl, GeomanDrawControl,
    LayersControl, ScaleControl, 
    Circle, CircleMarker, LayerGroup
)

from ipywidgets import Select, Dropdown
import matplotlib as plt
from shapely.geometry import mapping, shape
import json

def depot_selection_layers(depot_data, cell_data):
    depot_layers = {} # dict, where key is depot_id

    for feature in depot_data["features"]:
        depot_plots = [] # Hold range, centerpoint circles
        coords = feature["geometry"]["coordinates"]
        properties = feature["properties"]
        depot_radius = int(properties.get("depot_radius", 0))  # Default to 0 if missing
        min_encl_radius = int(properties.get("min_enclosing_rad", 0))  # Default to 0 if missing
        valid_depot_range = (depot_radius-min_encl_radius) if min_encl_radius>0 else 0

        depot_id = properties.get("depot_id", "Unknown ID")
        depot_name = f'Depot {depot_id}'

        # Find cells associated with each depot for coloration
        associated_cells = cell_data.copy()
        associated_cells['features'] = [feature for feature in cell_data['features']
                                        if feature['properties']['closest_depot'] == depot_id]

        # Add highlight to cells in depot range
        cells_layer = GeoJSON(
            data=associated_cells, 
            style={'color': 'red', 'fillColor': 'lightblue', 'opacity': 0.5, 'weight': 2},
            # style_callback=color_cells,
            name=associated_cells['name'])


        # Maximum range of depot
        range_circle = Circle(
            location=[coords[1], coords[0]],  # GeoJSON uses (lon, lat), Folium expects (lat, lon)
            radius=depot_radius,  # Circle radius in meters
            color='black', fill=False, fill_color='#3366cc',
            fill_opacity=0.05, weight=1,
            tooltip=f"Depot ID: {depot_id}\nRadius: {depot_radius}m"
        )

        # Plot our minimum enclosing circle
        min_enclosing_circle = Circle(
            location=[coords[1], coords[0]],  # GeoJSON uses (lon, lat), Folium expects (lat, lon)
            radius=min_encl_radius,  # Circle radius in meters
            color='green', fill=False, fill_color='#3366cc',
            fill_opacity=0.05, weight=1, opacity=0.15,
            tooltip=f"Depot ID: {depot_id}\nRadius: {min_encl_radius}m"
        )
        
        # All valid depot placements to cover all cells
        valid_depots_circle = Circle(
            location=[coords[1], coords[0]],  # GeoJSON uses (lon, lat), Folium expects (lat, lon)
            radius=valid_depot_range,  # Circle radius in meters
            color='green', fill=True, fill_color='green',
            fill_opacity=0.1, weight=1, opacity=0.35,
            tooltip=f"Valid depot range: {depot_id}\nRadius: {valid_depot_range}m"
        )

        center_circle = CircleMarker(
            location=[coords[1], coords[0]],  # GeoJSON uses (lon, lat), Folium expects (lat, lon)
            radius=5,  # Circle radius in meters
            color='black', fill=True, fill_color='red',
            fill_opacity=0.9, weight=1,
            tooltip=f"Depot ID: {depot_id}\nRadius: {depot_radius}m"
        )

        depot_layergroup = LayerGroup(
            layers=(cells_layer, range_circle, min_enclosing_circle, 
                    valid_depots_circle, center_circle),
            name=depot_name
        )
        depot_layers[depot_id] = depot_layergroup
    
    return depot_layers




def display_interactive_map(region_geojson, cells_geojson, depots_geojson, **file_layers):
    # Load Data for mapping
    # =====================

    # Load the GeoJSON region outline
    with open(region_geojson, "r") as f:
        region_contour_data = json.load(f)
    region_geometry = shape(region_contour_data['features'][0]['geometry'])
    region_center = region_geometry.centroid

    # Load Voronoi cells
    with open(cells_geojson, "r") as f:
        voronoi_data = json.load(f)

    # Load depot locations
    with open(depots_geojson, "r") as f:
        depot_data = json.load(f)



    # Set up interactive layer selections
    # ===================================
    all_depot_layers = depot_selection_layers(depot_data, voronoi_data) # Dict of layer instances
    list_depots = list(all_depot_layers.keys())

    # Depot select widget
    depot_select = Dropdown(
        options=list_depots,
        value=list_depots[0],
        description='Depot:',
        disabled=False
    )

    def on_depot_select(change):
        old_layer = all_depot_layers[change['old']]
        new_layer = all_depot_layers[change['new']]
        m.substitute(old_layer, new_layer)

    depot_select.observe(on_depot_select, names='value')




    # Set up interactive map
    # ======================
    m = Map(center=(region_center.y, region_center.x), zoom=16, scroll_wheel_zoom=True)

    # Add the region border to the map
    region_layer = GeoJSON(
        data=region_contour_data, 
        style={'color': 'blue', 'fillOpacity': 0.05, 'weight': 2},
        name=region_contour_data['name'])
    # region_layer.pmIgnore = True  # Lock this layer
    m.add(region_layer)

    # Add Voronoi polygons
    voronoi_layer = GeoJSON(
        data=voronoi_data, 
        style={'color': 'blue', 'fillColor': 'lightblue', 'opacity': 0.25, 'weight': 1},
        name=voronoi_data['name'])
    voronoi_layer.pmIgnore = True  # Lock this layer
    m.add(voronoi_layer)

    # Always keep depot points visible
    depot_points = GeoJSON(
        data=depot_data,
        style={'color': 'black', 'radius':3, 'fillColor': '#3366cc', 'opacity':0.5, 'weight':1.9, 'dashArray':'2', 'fillOpacity':0.6},
        hover_style={'fillColor': 'red' , 'fillOpacity': 0.2},
        point_style={'radius': 3, 'color': 'red', 'fillOpacity': 0.8, 'fillColor': 'blue', 'weight': 3},
        name=depot_data['name']
    )
    m.add(depot_points)

    # Add depot selection dropdown widget
    depot_select_control = WidgetControl(widget=depot_select, position='bottomright')
    m.add(depot_select_control)

    # Add (interactive + dynamic) depot layer
    depot_layer = all_depot_layers[depot_select.value] # Whichever is initially set
    m.add(depot_layer)

    # Add all args layers passed
    for layer_name, file_path in file_layers.items():
        with open(file_path, 'r') as f:
            data = json.load(f)
        layer = GeoJSON(data=data, name=layer_name)
        m.add_layer(layer)



    draw_control = GeomanDrawControl()
    draw_control.circlemarker = {}
    draw_control.rotate = False
    m.add(draw_control)

    m.add(FullScreenControl(position='topleft'))
    m.add(LayersControl(position='topright'))
    m.add(ScaleControl(position='bottomleft'))
    
    return m