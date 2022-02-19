# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 21:06:05 2021

@author: Joako360
"""
from collections import OrderedDict
from typing import Dict, Tuple
from extras import AIRMAP_ELEVATION_API_KEY, colors, custom_tags, map_geometries, networks
from transform import data_from_gdf, transform_gdf, transform_graph
from networkx import MultiDiGraph
import osmnx as ox
from osmnx._errors import EmptyOverpassResponse

ox.config(
    elevation_provider='airmap',
    log_console=True, 
    useful_tags_way=ox.settings.useful_tags_way + custom_tags)
ox.__version__
api_key=AIRMAP_ELEVATION_API_KEY
#custom_filter='["railway"~"tram|rail"]'
# download graph from OSM with osmnx parameters: place query, wich option and optional custom filters


def download_graph(place_query:str,which=1,cf=None)->MultiDiGraph:
    try:
        G = ox.graph_from_place(
            place_query, 
            network_type="drive_service", 
            simplify=False, 
            retain_all=True, 
            which_result=which, 
            custom_filter=cf
        )
        G = ox.simplify_graph(G)
        G = ox.add_node_elevations(G, api_key=api_key)
        G = ox.add_edge_grades(G)
        G = ox.add_edge_bearings(G)
        print("Success!")
        return G
    except ValueError:
        print("Found no graph nodes within the requested polygon.")
        G = None
        return G
    except EmptyOverpassResponse:
        print("There are no data elements in the response JSON")
        G = None
        return G

# Ask for a place, makes a Nominatim query and prints the results in a table
# Returns a tuple of the place name and the index of the result chosen by the user


def download_menu()->Tuple:
    
    place=input(
        '''Enter the city name, which will also be the file name. 
        A list of results will be displayed.
        Hint: City may be OSM admin_level = 7+: '''
        ).title()
    if place == '0':
        return None, None
    nmntm_req = OrderedDict([('q',place),('format','json')])
    nmntm_res = ox.downloader.nominatim_request(nmntm_req)
    
    while len(nmntm_res) == 0:
        print("No results. Hint: City may be OSM admin_level = 7+")
        place = input("Enter the city name, which will also be the file name. (Enter 0 for exit): ").title()
        if place == '0':
            return None, None
            break
        nmntm_req = OrderedDict([('q',place),('format','json')])
        nmntm_res = ox.downloader.nominatim_request(nmntm_req)
    
    print("{:<6}║{:<50}║{:<14}║{:<10}".format('Option','Display name','Type','Class'))
    print('═' * 6 + '╬' + '═' * 50 + '╬' + '═' * 14 + '╬' + '═' * 10)
    for idx, result in enumerate(nmntm_res,start=1):
        result_line = "{:<6}║{:<50}║{:<14}║{:<10}".format(str(idx), result['display_name'][:50], result['type'][:14], result['class'][:10])
        if result['type'] == 'administrative' or result['class'] == 'boundary':
            print(colors.bgGreen + result_line + colors.reset)
        elif result['osm_type'] != 'relation':
            print(colors.bgRed + result_line + colors.reset)
        else:
            print(result_line)
    which = int(input("Which result? {option}\nHint: cities may have \"administrative boundary\" tag.: "))
    return (place, which)

def download_data(place:str, which:int)->Dict:
    d = {}
    if not which:
        return d
    area = ox.geocode_to_gdf(place, which_result=which)
    d = data_from_gdf(area)
    
    x_0 = d['x_0']
    y_0 = d['y_0']
    
    for typ, tag in map_geometries.items():
        print("Acquiring {} areas data".format(typ))
        gdf = ox.geometries_from_place(place, tag ,which_result=which)
        if not gdf.empty:
            gdf_trns = transform_gdf(gdf, x_0, y_0)
            d[typ] = gdf_trns
        else:
            d[typ] = None
        
    for typ, cf in networks.items():
        print("Acquiring {} network data".format(typ))
        G = download_graph(place, which=which, cf=cf)
        if G is not None:
            G_trns = transform_graph(G, x_0, y_0)
            d[typ] = G_trns
            print("Success!")
        else:
            print("GeoDataFrame seems to be empty...")
            d[typ] = None

    return d

    