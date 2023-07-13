#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
  - Nick Ackerley <nicholas.ackerley@nrcan-rncan.gc.ca>
"""

import configparser
import dash
import json
import requests

from dash import html, callback
from dash.dcc import Tooltip, Graph, Tab, Tabs
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
from dash_leaflet import (Map,
                          TileLayer,
                          LayersControl,
                          BaseLayer,
                          WMSTileLayer,
                          GeoJSON)
from dash_extensions.enrich import (Output,
                                    DashProxy,
                                    Input,
                                    MultiplexerTransform)
from dash_extensions.javascript import arrow_function


from plotly.graph_objects import Heatmap
from plotly.subplots import make_subplots
import plotly.graph_objects as go

dash.register_page(__name__, path='/')


def get_config_params(args):
    """Parse configuration from supplied file."""
    config_obj = configparser.ConfigParser()
    config_obj.read(args)
    return config_obj


def read_targets_geojson():
    """Query VRRC API for All Targets FootPrints"""
    try:
        response = requests.get('http://127.0.0.1:8081/targets/geojson')
        response_geojson = json.loads(response.content)
    except requests.exceptions.ConnectionError:
        response_geojson = None
        # pass
    return response_geojson


targets_geojson = read_targets_geojson()
config = get_config_params('scripts/config.ini')
GEOSERVER_ENDPOINT = config.get('geoserver', 'geoserverEndpoint')

INITIAL_TARGET = 'Meager_5M10'

# basemap configuration
BASEMAP_URL = (
    'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer'
    '/tile/{z}/{y}/{x}')
BASEMAP_ATTRIBUTION = (
    'Tiles courtesy of the '
    '<a href="https://usgs.gov/">U.S. Geological Survey</a>')
BASEMAP_NAME = 'USGS Topo'

# TODO read target configuration from database
TARGET_CENTRES = {
    'Meager_5M10': [50.64, -123.60]
}

# spatial_view = html.Div()
layout = html.Div(children=[
    html.H3('VRRC Volcano InSAR Monitoring System - National Overview', 
            style={'text-align': 'center'}),
    html.Div(Map(
        [
            TileLayer(),
            LayersControl(
                BaseLayer(
                    TileLayer(
                        url=BASEMAP_URL,
                        attribution=BASEMAP_ATTRIBUTION
                    ),
                    name=BASEMAP_NAME,
                    checked=True
                ),
            ),
            # WMSTileLayer(
            #     url=f'{GEOSERVER_ENDPOINT}/vectorLayers/wms?',
            #     layers='cite:permanent_snow_and_ice_2',
            #     format='image/png',
            #     transparent=True,
            #     opacity=1.0),
            GeoJSON(data=targets_geojson,
                    options=dict(color='red'),
                    zoomToBounds=True,
                    zoomToBoundsOnClick=True,
                    id='sites',
                    hoverStyle=arrow_function(dict(weight=5,
                                                   color='#666',
                                                   dashArray='')))
        ],
        id='interferogram-bg',
        center=TARGET_CENTRES[INITIAL_TARGET],
        zoom=12,
    ),
    style={'height': '90vh'},
    ),
    html.Div(id="site")
    
        ],
    # Tooltip(id="site-tooltip")
)


@callback(Output("site", "children"),
          Input("sites", "hover_feature"))
def state_hover(feature):
    if feature is not None:
        children = [
                    html.Div([
                        f"{feature['properties']['name_en']}"
                        ], style={'width': '200px', 'white-space': 'normal'})
                    ]
        return children
