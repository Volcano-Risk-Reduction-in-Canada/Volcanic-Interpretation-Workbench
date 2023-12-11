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

from dash import html, callback, dash_table
from dash.dcc import Tooltip, Graph, Tab, Tabs, Markdown
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

import pandas as pd
import plotly.graph_objects as go

dash.register_page(__name__, path='/')

df = pd.read_csv('app/Data/home_test_table.csv')

def get_config_params(args):
    """Parse configuration from supplied file."""
    config_obj = configparser.ConfigParser()
    config_obj.read(args)
    return config_obj


def read_targets_geojson():
    """Query VRRC API for All Targets FootPrints"""
    try:
        response = requests.get('http://127.0.0.1:8080/targets/geojson')
        response_geojson = json.loads(response.content)
    except requests.exceptions.ConnectionError:
        response_geojson = None
        # pass
    return response_geojson


targets_geojson = read_targets_geojson()
config = get_config_params('scripts/config.ini')
GEOSERVER_ENDPOINT = config.get('geoserver', 'geoserverEndpoint')

# basemap configuration
BASEMAP_URL = (
    'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer'
    '/tile/{z}/{y}/{x}')
BASEMAP_ATTRIBUTION = (
    'Tiles courtesy of the '
    '<a href="https://usgs.gov/">U.S. Geological Survey</a>')
BASEMAP_NAME = 'USGS Topo'

# spatial_view = html.Div()
layout = html.Div([
    html.H3('VRRC InSAR - National Overview', 
            style={'text-align': 'center'}),
    html.Div(
        id='interferogram-bg',
        style={'width': '100%', 'height': '100vh', 'position': 'relative'},
        children=[
            Map(
                style={'width': '100%', 'height': '100%'},
                center=[54.64, -123.60],
                zoom=6,
                children=[
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
                    GeoJSON(
                        data=targets_geojson,
                        options=dict(
                            style=dict(color='red')
                        ),
                        zoomToBounds=False,
                        zoomToBoundsOnClick=True,
                        id='geojson',
                        hoverStyle=arrow_function(dict(weight=5,
                                                        color='#666',
                                                        dashArray=''))
                    ),
                    html.Div(
                        id="popup-output",
                        style={"position": "absolute",
                               "pointer-events": "all",
                               "display": "none"}),
                ]
            ),
            # Style for custom popup
            Markdown("""
                .popup {
                    background-color: black;
                    border: 1px solid #ccc;
                    padding: 5px;
                    max-width: 200px;
                }
            """),
        ]
    ),
    html.Div(
        id='table-container',
        style={'position': 'absolute',
               'bottom': '200px',
               'right': '2%',
               'width': '20%',
               'zIndex': 1000},
        children=[
            dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                style_table={'color': 'black'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'Unrest', 'row_index': i},
                        'color': 'red' if unrest else 'green',
                    } for i, unrest in enumerate(df['Unrest'])
                ],
            )
        ]
    ),

])

@callback(
    Output("hover-output", "children"),
    Input("geojson", "hover_feature"),
)
def display_hover_info(hover_feature):
    if hover_feature is not None:
        return [
            html.Div(
                className="popup",
                children=[
                    html.Div(f"Name: {hover_feature['properties']['name']}"),
                    html.Div(f"Info: {hover_feature['properties']['info']}"),
                ],
                id="popup-div",
            )
        ]

    return []


clientside_callback(
    """
    function updatePopupPosition(hoverFeature) {
        if (hoverFeature) {
            var popupDiv = document.getElementById("popup-div");
            popupDiv.style.display = "block";
            popupDiv.style.left = hoverFeature.layerPoint.x + "px";
            popupDiv.style.top = hoverFeature.layerPoint.y + "px";
        } else {
            var popupDiv = document.getElementById("popup-div");
            popupDiv.style.display = "none";
        }
    }
    """,
    Output("popup-container", "children"),
    Input("geojson", "hover_feature"),
)

# @callback(Output("site", "children"),
#           Input("sites", "hover_feature"))
# def state_hover(feature):
#     if feature is not None:
#         children = [
#                     html.Div([
#                         f"{feature['properties']['name_en']}"
#                         ], style={'width': '200px', 'white-space': 'normal'})
#                     ]
#         return children
