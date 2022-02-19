# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 20:27:25 2021

@author: Joako360
"""
from download import download_menu, download_data
from heightmapper import heightmapper
from os import name, system

class map_data:
    def __init__(self):
        self.data = {}
        self.bounds = {}
        self.heightmap = [[]]

map = map_data()

def dlcity()->None:
    clear()
    place,which = download_menu()
    map.data = download_data(place, which)
    map.bounds = {
        'N': map.data['area']['bbox_north'][0],
        'S': map.data['area']['bbox_south'][0],
        'E': map.data['area']['bbox_east'][0],
        'W': map.data['area']['bbox_west'][0]       
    }

def load()->None:
    print('loading...')

def save()->None:
    print('saving...')

def export()->None:
    if map.bounds != {}:
        map.heightmap = heightmapper(map.bounds)
        
def exit()->None:
    print('exit...')
    
def clear()->None:
    if name == 'nt':
        system('cls')
    else:
        system('clear')

# menu class with labels and function calls for each option

class Menu:
    label = {}
    func = {}
    def __init__(self, title, label, func):
        self.title = title
        self.label = label
        self.func = func
    def show(self):
        #clear()
        print('\n' + '-'*len(self.title))
        print(self.title)
        print('-'*len(self.title))
        for key,value in self.label.items():
            print(f'{key}. {value}')
    def run(self):
        while True:
            self.show()
            choice = input('\nChoose an option: ')
            if choice in self.func:
                self.func[choice]()
            else:
                print('\n' + '*'*len(self.title))
                print('*'*len(self.title))
                print(f'{choice} is not a valid option')
                print('*'*len(self.title))
                input('\npress enter to continue...')

# main menu object
mainmenu = Menu('Main Menu', {
    '1': 'Download City',
    '2': 'Load',
    '3': 'Save',
    '4': 'Export',
    '5': 'Exit'
}, {
    '1': dlcity,
    '2': load,
    '3': save,
    '4': export,
    '5': exit
})
mainmenu.run()
