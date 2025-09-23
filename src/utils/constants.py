"""
Constants and configuration for OSM2terrn project.

This module defines global constants, OSM tags, map geometry categories, network filters,
and terminal color codes for formatting output.
"""

import os

EARTH_MIN_ELEVATION = -11000  # Minimum elevation on Earth in meters (Mariana Trench)
EARTH_MAX_ELEVATION = 8850     # Maximum elevation on Earth in meters (Mount Everest)

def get_opentopo_elevation_api_key():
    import os
    return os.environ.get('OPENTOPO_ELEVATION_API_KEY', '')
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
# Each category has its own dict of type:tag pairs named like in OSM map features.
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
        'leisure': 'park',
    },
    'lakes': {
        'natural': 'water',
        'water': ['lake', 'river'],  # Use a list for multiple types
    },
}

# Dictionary of networks, such as roads, rails or rivers.
# Values are string literal single quoted list of tags, used for custom filter download from OSM.
networks = {
    'roads': None,
    'rails': '["railway"~"tram|rail"]',
    'rivers': '["waterway"~"river|stream|canal"]',
}

class Colors:
    """
    ANSI color escape sequences for formatting terminal output text.
    """
    reset = "\033[0m"

    # Black
    fg_black = "\033[30m"
    fg_bright_black = "\033[30;1m"
    bg_black = "\033[40m"
    bg_bright_black = "\033[40;1m"

    # Red
    fg_red = "\033[31m"
    fg_bright_red = "\033[31;1m"
    bg_red = "\033[41m"
    bg_bright_red = "\033[41;1m"

    # Green
    fg_green = "\033[32m"
    fg_bright_green = "\033[32;1m"
    bg_green = "\033[42m"
    bg_bright_green = "\033[42;1m"

    # Yellow
    fg_yellow = "\033[33m"
    fg_bright_yellow = "\033[33;1m"
    bg_yellow = "\033[43m"
    bg_bright_yellow = "\033[43;1m"

    # Blue
    fg_blue = "\033[34m"
    fg_bright_blue = "\033[34;1m"
    bg_blue = "\033[44m"
    bg_bright_blue = "\033[44;1m"

    # Magenta
    fg_magenta = "\033[35m"
    fg_bright_magenta = "\033[35;1m"
    bg_magenta = "\033[45m"
    bg_bright_magenta = "\033[45;1m"

    # Cyan
    fg_cyan = "\033[36m"
    fg_bright_cyan = "\033[36;1m"
    bg_cyan = "\033[46m"
    bg_bright_cyan = "\033[46;1m"

    # White
    fg_white = "\033[37m"
    fg_bright_white = "\033[37;1m"
    bg_white = "\033[47m"
    bg_bright_white = "\033[47;1m"
