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

def translate_gdf(gdf:GeoDataFrame, x_0=None, y_0=None)->tuple:
    d = {}
    
    if x_0 == None and y_0 == None:
        # if offset coordenates are unknoun, must be the area and this function
        # calculate that offset
        x_0, y_0 = float(gdf.bounds.minx), float(gdf.bounds.maxy)
        size_x, size_y = ceil(gdf.bounds.maxx-gdf.bounds.minx),ceil(gdf.bounds.maxy-gdf.bounds.miny)
        # must be square, so pick the greater
        world_size = size_x if size_x >= size_y else size_y
        d = {
            'x_0': x_0,
            'y_0': y_0,
            'size_x': size_x,
            'size_y': size_y,
            'world_size': world_size
        }

    gdf_trns = gdf  #I make this so gdf_trns is also a DataFreme, otherwise is just a Series
    gdf_trns['geometry'] = gdf['geometry'].apply(affinity.translate,xoff=-x_0,yoff=-y_0)
    
    if d != {}:
        d['area'] = gdf_trns
        return d
    else:
        return gdf_trns

def translate_graph(G:MultiDiGraph,x_0:float,y_0:float)->MultiDiGraph:  #networks use only
    nodes, edges = graph_to_gdfs(G)
    nodes_trns = translate_gdf(nodes,x_0,y_0); edges_trns = translate_gdf(edges,x_0,y_0)
    G_trns = graph_from_gdfs(nodes_trns,edges_trns)
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
        