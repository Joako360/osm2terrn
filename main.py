# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 20:27:25 2021

@author: Joako360
"""
from download import download_menu, download_data
from heightmapper import heightmapper
from os import name, system
data = {}
bounds = {}
heightmap = [[]]
def dlcity()->None:
    global data
    global bounds
    place,which = download_menu()
    data = download_data(place, which)
    bounds = {
        'N': data['area']['bbox_north'][0],
        'S': data['area']['bbox_south'][0],
        'E': data['area']['bbox_east'][0],
        'W': data['area']['bbox_west'][0]       
    }

def load()->None:
    print('loading...')

def save()->None:
    print('saving...')

def export()->None:
    global heightmap
    if bounds != {}:
        heightmap = heightmapper(bounds)
        
def exit()->None:
    print('exit...')
    
def clear()->None:
    if name == 'nt': 
        _ = system('cls')
    else: 
        _ = system('clear')

class Menu:
    label={
        '1':'Download from Internet',
        '2':'Load GraphML/OSM XML',
        '3':'Save GraphML/OSM XML',
        '4':'Export GeoPackage/ESRI Shapefile/RoR files',
        '5':'Exit app'
        }
    func={
        '1':dlcity,
        '2':load,
        '3':save,
        '4':export,
        '5':exit
        }
    
def show_menu(title:str,menu:Menu)->None:
    print(title)
    options = menu.keys()
    options = sorted(options)
    for entry in options: 
        print (entry, menu[entry])
    
def main_menu()->None:
    is_saved=False
    m=Menu
    clear()
    while(True):
        show_menu('Main Menu v0.1',m.label)
        choice=input("Pick an opt: ")
        if choice == '3':
            is_saved=True
        if choice == '5':
            # if is_saved==False:
            #     print("Warning: Project not saved, proceed? y/[n]:")
            # else:
            break
        m.func.get(choice)()
        
