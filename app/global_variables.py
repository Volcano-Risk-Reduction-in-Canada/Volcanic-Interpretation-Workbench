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

# basemap configuration
BASEMAP_URL = (
    'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer'
    '/tile/{z}/{y}/{x}')
BASEMAP_ATTRIBUTION = (
    'Tiles courtesy of the '
    '<a href="https://usgs.gov/">U.S. Geological Survey</a>')
BASEMAP_NAME = 'USGS Topo'

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
