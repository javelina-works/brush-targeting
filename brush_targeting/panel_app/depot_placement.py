import panel as pn
import param
import geopandas as gpd
import json

from brush_targeting.plant_search.region_partition import centroidal_voronoi_tessellation


class DepotPlacement(param.Parameterized):
    target_area_acres = param.Number(default=0.5, step=0.25, doc="How large in acres each cell should approximately be.")
    max_iterations = param.Integer(default=15, bounds=(3,45), doc="Number of iterations to determine tesselation for work region")
    region_outline_gdf = param.ClassSelector(class_=gpd.GeoDataFrame, doc="Region to tesselate into cells")
    cells_gdf = param.ClassSelector(class_=gpd.GeoDataFrame, default=None, allow_None=True, doc="Region tesselated into cells")
    cells_geojson = param.Dict(default=None, doc="GeoJSON of the region partitioning.")
