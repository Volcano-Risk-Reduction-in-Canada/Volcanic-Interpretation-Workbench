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
import json
import dash
import requests

from dash import html, dash_table, dcc, callback
import dash_bootstrap_components as dbc
from dash_leaflet import (Map,
                          TileLayer,
                          LayersControl,
                          BaseLayer,
                          GeoJSON)
from dash_extensions.enrich import (Output,
                                    Input,
                                    State)
from dash_extensions.javascript import (assign,
                                        arrow_function)

import pandas as pd

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
        for feature in response_geojson['features']:
            feature['properties']['tooltip'] = feature['id']

    except requests.exceptions.ConnectionError:
        response_geojson = None
        # pass
    return response_geojson


targets_geojson = read_targets_geojson()
# print(targets_geojson['features'][0]['properties']['name_en'])
on_each_feature = assign("""function(feature, layer, context){
    layer.bindTooltip(`${feature.properties.name_en}`)
}""")
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
    dcc.Location(id='url', refresh=True),
    dcc.Store(id='selected_feature'),
    html.H3(
        id='Title',
        children='VRRC InSAR - National Overview',
        style={'text-align': 'center'}),
    html.Div(
        id='interferogram-bg',
        style={'width': '100%', 'height': '100vh', 'position': 'relative'},
        children=[
            Map(
                id='map',
                style={'width': '100%', 'height': '95vh'},
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
                    # Popup(position=[57, 10], children="Hello world!"),
                    GeoJSON(
                        data=targets_geojson,
                        options=dict(
                            style=dict(color='red')
                        ),
                        zoomToBounds=False,
                        zoomToBoundsOnClick=False,
                        id='geojson',
                        # onEachFeature=on_each_feature,
                        # children=[
                        #     Tooltip(
                        #         id='geojson_tooltip',
                        #         interactive=True,
                        #         content="This is <b>html<b/>!")],
                        hoverStyle=arrow_function(dict(weight=5,
                                                        color='#666',
                                                        dashArray=''))
                    ),
                ]
            ),
        ]
    ),
    html.Div(
        id='table-container',
        style={'position': 'absolute',
               'top': '125px',
               'right': '0.7%',
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


# @callback(
#     Output('selected_feature', 'data'),
#     [Input('geojson', 'click_feature')]
# )
# def update_selected_feature(feature):
#     if feature is not None:
#         return feature['properties']
#     return {}


# Callback to navigate to a new page based on the selected feature
@callback(
    [Output('selected_feature', 'data'),
     Output('url', 'pathname'),
     Output('map', 'children')],
    [Input('map', 'click_lat_lng')],
    [State('geojson', 'data')],
    prevent_initial_call=True
)
def handle_map_click(click_lat_lng, geojson_data):
    selected_feature = {}
    new_page_path = '/'
    map_children = [
        TileLayer(),
        GeoJSON(data=geojson_data, id='geojson', click_feature_event='click'),
    ]

    if click_lat_lng is not None:
        for feature in geojson_data['features']:
            geometry = feature.get('geometry', {})
            if geometry.get('type') == 'Polygon' and dl.inside_polygon(click_lat_lng, geometry.get('coordinates', [[]])):
                selected_feature = feature['properties']
                new_page_path = '/new_page'
                map_children = [
                    html.H3(f"Additional information about {selected_feature.get('name_en', 'Unknown')}"),
                    # Add more components to display additional information as needed
                ]
                break

    return selected_feature, new_page_path, map_children
