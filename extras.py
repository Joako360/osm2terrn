# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 23:31:05 2021

@author: Joako360
"""
AIRMAP_ELEVATION_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' \
                           '.eyJjcmVkZW50aWFsX2lkIjoiY3JlZGVudGlhbHxBUkFBNW1XaVB4Tk9XTkNKNmtHdmxpNm05TVpnIiwiYXBwbGljYXRpb25faWQiOiJhcHBsaWNhdGlvbnxNcUp4a0pQdUp6UEcwa2ZPZHo2cFJpMzBCNG9rIiwib3JnYW5pemF0aW9uX2lkIjoiZGV2ZWxvcGVyfGI5encyS2dDZEFFQWc5SWE0YVJ2TmllNmVER0UiLCJpYXQiOjE2MTU5ODk0NzZ9.apf5s2zrCn3Cv81SyJrVPsVVZeKrBmITdWDcDXYZMvs '
AIRMAP_CLIENT_ID = '2bac4e5e-8ece-4f58-ba36-09ee5a669574'
# List of custom tags added in the osmnx configuration
custom_tags = [
    'aerialway',
    'aeroway',
    'cycleway',
    'footway',
    'railway',
    'waterway',
    ]
# Dictionary of areas in the map, such as buildings footprint, parks or lakes.
# Each category has its own dict of type:tag pairs named like in OSM map fratures.
map_geometries = {
    'buildings': {
        'amenity': 'school',
        'building': True,
        'sport': 'stadium',
        'tourism': 'museum',
        },
    'parks': {
        'landuse': 'grass',
        'natural': 'wood',
        'leisure': 'park'
        },
    'lakes': {
        'natural': 'water',
        'water': 'lake',
        'water': 'river',
        }
    }
# Dictionary of networks, such as roads, rails or rivers. 
# Values are string literal single quoted list of tags, used for custom filter download from OSM.
networks = {
    'roads': None,
    'rails': '["railway"~"tram|rail"]',
    'rivers': '["waterway"~"river|stream|canal"]'
    }
# Class of ANSI colors escape sequences for formatting terminal output text
class colors:
    reset = "\033[0m"

    # Black
    fgBlack = "\033[30m"
    fgBrightBlack = "\033[30;1m"
    bgBlack = "\033[40m"
    bgBrightBlack = "\033[40;1m"

    # Red
    fgRed = "\033[31m"
    fgBrightRed = "\033[31;1m"
    bgRed = "\033[41m"
    bgBrightRed = "\033[41;1m"

    # Green
    fgGreen = "\033[32m"
    fgBrightGreen = "\033[32;1m"
    bgGreen = "\033[42m"
    bgBrightGreen = "\033[42;1m"

    # Yellow
    fgYellow = "\033[33m"
    fgBrightYellow = "\033[33;1m"
    bgYellow = "\033[43m"
    bgBrightYellow = "\033[43;1m"

    # Blue
    fgBlue = "\033[34m"
    fgBrightBlue = "\033[34;1m"
    bgBlue = "\033[44m"
    bgBrightBlue = "\033[44;1m"

    # Magenta
    fgMagenta = "\033[35m"
    fgBrightMagenta = "\033[35;1m"
    bgMagenta = "\033[45m"
    bgBrightMagenta = "\033[45;1m"

    # Cyan
    fgCyan = "\033[36m"
    fgBrightCyan = "\033[36;1m"
    bgCyan = "\033[46m"
    bgBrightCyan = "\033[46;1m"

    # White
    fgWhite = "\033[37m"
    fgBrightWhite = "\033[37;1m"
    bgWhite = "\033[47m"
    bgBrightWhite = "\033[47;1m"
