# -*- coding: utf-8 -*-
"""
Created on Thu Apr  1 16:52:21 2021

@author: joako360
"""
from download import download_menu, download_data
from transform import translate_gdf
import osmnx as ox

tobj = open("roads.tobj","w+")
tobj.write("// x        y        z    rx  ry rz odefname (without .odef file extension)\n")

data = download_data(*download_menu())
x_0 = data['x_0']; y_0 = data['y_0']
nodes=ox.graph_to_gdfs(data['roads'],nodes=True,edges=False)
nodes_trns=translate_gdf(nodes, x_0, y_0)
tobj.write("//some roads\n")

for index,row in nodes_trns.iterrows():
    y=float(row['elevation'])
    coords=str(row['geometry'])[6:]
    coords=coords.replace('(','').replace(')','')
    [x,z]=coords.split()
    x=float(x)
    z=float(z)*-1.0
    tobj.write("{}, {}, {}, 0.0, 0.0, 0.0, road-crossing\n".format(str(x),str(y),str(z)))
    
tobj.close()