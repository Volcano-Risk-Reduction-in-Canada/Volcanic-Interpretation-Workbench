#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Chloe Lam <chloe.lam@nrcan-rncan.gc.ca>
"""
import boto3

s3 = boto3.client('s3')

# basemap configuration (used by the Leaflet map on the overview page)
BASEMAP_URL = (
    'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer'
    '/tile/{z}/{y}/{x}')
BASEMAP_ATTRIBUTION = (
    'Tiles courtesy of the '
    '<a href="https://usgs.gov/">U.S. Geological Survey</a>')
BASEMAP_NAME = 'USGS Topo'

# basemap configuration for the MapLibre 3D map on the site page.
# Esri's ArcGIS Online basemaps are free/token-free and, unlike
# BASEMAP_URL above, have true global coverage (the site page covers
# volcanoes in BC, Alaska, Iceland, Italy, Russia, and Indonesia).
ESRI_ATTRIBUTION = (
    'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
)
MAPLIBRE_BASEMAPS = {
    'topo': {
        'url': (
            'https://server.arcgisonline.com/ArcGIS/rest/services/'
            'World_Topo_Map/MapServer/tile/{z}/{y}/{x}'
        ),
        'attribution': ESRI_ATTRIBUTION,
        'label': 'Topography',
    },
    'streets': {
        'url': (
            'https://server.arcgisonline.com/ArcGIS/rest/services/'
            'World_Street_Map/MapServer/tile/{z}/{y}/{x}'
        ),
        'attribution': ESRI_ATTRIBUTION,
        'label': 'Streets',
    },
    'imagery': {
        'url': (
            'https://server.arcgisonline.com/ArcGIS/rest/services/'
            'World_Imagery/MapServer/tile/{z}/{y}/{x}'
        ),
        'attribution': ESRI_ATTRIBUTION,
        'label': 'Imagery',
    },
    # Virtual entry: no tiles of its own -- reuses 'topo's raster layer
    # with a hillshade layer (from the same DEM source used for terrain)
    # draped on top. See MapLibreMap.react.js's buildBaseStyle/
    # addHillshadeLayer/setActiveBasemap for how 'hillshade'/'baseKey'
    # are handled.
    'topoHillshade': {
        'label': 'Topography (Hillshade)',
        'baseKey': 'topo',
        'hillshade': True,
    },
}
MAPLIBRE_DEFAULT_BASEMAP = 'topo'

# DEM terrain configuration for the MapLibre 3D map. Uses AWS Open Data's
# free, global, token-free Terrarium-encoded elevation tiles (SRTM/GMTED/
# ETOPO1 sourced) -- no per-site generation pipeline needed. Routed
# through the /getDemTileUrl same-origin proxy (see routes.py) because
# the upstream bucket only advertises CORS on OPTIONS preflight
# requests, not on the actual GET responses -- MapLibre needs to decode
# DEM tile pixels client-side, so a CORS-tainted image silently yields
# flat (zero-elevation) terrain instead of an error.
DEM_TILE_URL = '/getDemTileUrl?z={z}&x={x}&y={y}'
DEM_ENCODING = 'terrarium'
DEM_TERRAIN_EXAGGERATION = 1.5

# coherence plotting configuration
YEAR_AXES_COUNT = 1
BASELINE_MAX = 150
BASELINE_DTICK = 24
YEARS_MAX = 5
CMAP_NAME = 'RdBu_r'
COH_LIMS = (0.2, 0.4)
TEMPORAL_HEIGHT = 300
MAX_YEARS = 3
DAYS_PER_YEAR = 365.25

# styling for legend text
LEGEND_TEXT_STYLING = {
    "color": "black",
    "font-size": "12px",
    "vertical-align": "middle"
}

# styling for legend button
LEGEND_BUTTON_STYLING = {
    **LEGEND_TEXT_STYLING,
    "position": "absolute",
    "top": "10px",
    "background-color": "white",
    "padding": "5px",
    "borderRadius": "5px",
    "border": "1px solid #ccc",
    "z-index": "2000"
}

LEGEND_PLACEMENT_STYLING = {
    "position": "absolute",
    "bottom": "30px",
    "right": "12px",
    "background-color": "red",
    "z-index": "2000"
}
