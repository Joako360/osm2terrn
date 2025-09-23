import matplotlib.pyplot as plt
import osmnx as ox
from extras import AIRMAP_ELEVATION_API_KEY, custom_tags
from transform import translate_gdf


ox.config(elevation_provider='airmap',log_console=True,useful_tags_way=ox.settings.useful_tags_way + custom_tags)
api_key = AIRMAP_ELEVATION_API_KEY
ox.__version__
# get the street network for luis guillon
place = 'Luis Guillón, Buenos Aires, Argentina'
place_query = {'city':'Luis Guillón', 'state':'Buenos Aires', 'country':'Argentina'}
G = ox.graph_from_place(place_query,'["waterway"~"river|stream|canal"]')
G = ox.add_node_elevations(G, api_key=api_key)
G = ox.add_edge_bearings(G)
G = ox.add_edge_grades(G)
G_proj = ox.project_graph(G)
nodes, edges=ox.graph_to_gdfs(G_proj)
area=ox.geocode_to_gdf(place_query)
area_proj=ox.project_gdf(area)
area_trns,x_0,y_0,size_x,size_y,world_size=translate_gdf(area_proj)
nodes_trns=translate_gdf(nodes,x_0,y_0)
edges_trns=translate_gdf(edges,x_0,y_0)

# buildings=ox.geometries_from_place(place_query,{'building': True})
fig, ax = plt.subplots(figsize=[12,8])
area_trns.plot(ax=ax,facecolor='k')
edges_trns.plot(ax=ax,linewidth=1)
# buildings.plot(ax=ax,facecolor='r',alpha=0.5)
# lat=np.arange(area.bbox_south[0],area.bbox_north[0],1/3600)
# lon=np.arange(area.bbox_west[0],area.bbox_east[0],1/3600)
