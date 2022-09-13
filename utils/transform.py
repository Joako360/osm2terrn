# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 09:54:16 2021

@author: Joako360
"""
from math import ceil
from geopandas import GeoDataFrame
from networkx import MultiDiGraph
from osmnx import graph_from_gdfs, graph_to_gdfs, project_graph, project_gdf
from shapely import affinity

# extract offset, x size, y size, map size and the itself from GeoDataFrame and return dict.
def data_from_gdf(gdf:GeoDataFrame)->dict:
    d = {
        'x_0': float(gdf.bounds.minx),
        'y_0': float(gdf.bounds.maxy),
        'x_size': ceil(gdf.bounds.maxx - gdf.bounds.minx),
        'y_size': ceil(gdf.bounds.maxy - gdf.bounds.miny),
        'world_size': ceil(gdf.bounds.maxx - gdf.bounds.minx) * ceil(gdf.bounds.maxy - gdf.bounds.miny),
        'area': gdf
    }
    return d
# translate GeoDataFrame with same CRS and bounds to new coordinates with x_0,y_0 as the new origin
def translate_gdf(gdf:GeoDataFrame, x_0=None, y_0=None)->GeoDataFrame:
    if x_0 is None: x_0 = gdf.bounds.minx
    if y_0 is None: y_0 = gdf.bounds.maxy
    gdf_trns = gdf.copy()
    gdf_trns = affinity.translate(gdf,xoff=x_0, yoff=y_0)
    return gdf_trns


def translate_graph(G:MultiDiGraph,x_0:float,y_0:float)->MultiDiGraph:  #networks use only
    G_trns = G.copy()
    G_trns.graph['x_0'] = x_0
    G_trns.graph['y_0'] = y_0
    for node in G_trns.nodes():
        G_trns.nodes[node]['x'] -= x_0
        G_trns.nodes[node]['y'] -= y_0
    return G_trns

def transform_gdf(gdf:GeoDataFrame,x_0=None, y_0=None)->tuple:
    if len(gdf['geometry']) != 0:
        gdf_proj = project_gdf(gdf)
        gdf_trns = translate_gdf(gdf_proj,x_0,y_0)
        return gdf_trns
    else:
        print("GeoDataFrame must have a valid CRS and cannot be empty")
        return gdf
    
def transform_graph(G:MultiDiGraph,x_0:float, y_0:float)->tuple:  #networks use only
    G_proj = project_graph(G)
    G_trns = translate_graph(G_proj,x_0,y_0)
    return G_trns
        