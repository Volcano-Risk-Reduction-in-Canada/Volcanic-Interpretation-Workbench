#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Chloe Lam <chloe.lam@nrcan-rncan.gc.ca>
"""
from app.data_utils import build_summary_table, get_config_params, read_targets_geojson

config = get_config_params()
targets_geojson = read_targets_geojson()
summary_table_df = build_summary_table(targets_geojson)

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
