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
import requests
import datetime

from io import StringIO

import dash
from dash import html, dash_table, dcc, callback
from dash_leaflet import (Map,
                          TileLayer,
                          LayersControl,
                          BaseLayer,
                          CircleMarker,
                          Popup,
                          Marker,
                          Tooltip)
from dash_extensions.enrich import (Output,
                                    Input)
from dash_extensions.javascript import (assign)

import numpy as np
import pandas as pd

dash.register_page(__name__, path='/')


def get_config_params(args):
    """Parse configuration from supplied file."""
    config_obj = configparser.ConfigParser()
    config_obj.read(args)
    return config_obj


def calculate_centroid(coords):
    """Calculate a centroid given a list of x,y coordinates"""
    num_points = len(coords)
    total_x = 0
    total_y = 0
    for x, y in coords:
        total_x += x
        total_y += y
    centroid_x = total_x / num_points
    centroid_y = total_y / num_points
    return [centroid_x, centroid_y]


def calculate_and_append_centroids(geojson_dict):
    "append polygon centroid to geojson object"
    for feature in geojson_dict['features']:
        geometry = feature['geometry']
        centroid = calculate_centroid(geometry['coordinates'][0])
        feature['geometry']['type'] = 'Point'
        feature['geometry']['coordinates'] = centroid


def read_targets_geojson():
    """Query VRRC API for All Targets FootPrints"""
    try:
        # response = requests.get('http://127.0.0.1:8080/targets/geojson')
        # response_geojson = json.loads(response.content)
        unrest_table_df = pd.read_csv('app/Data/unrest_table.csv')
        with open("app/Data/sites.geojson") as sites_geojson:
            response_geojson = json.load(sites_geojson)
        calculate_and_append_centroids(response_geojson)
        for feature in response_geojson['features']:
            if unrest_table_df.loc[unrest_table_df['Site']==
                                   feature['properties']['name_en']]['Unrest'].values.size > 0 :
                unrest_bool = unrest_table_df.loc[unrest_table_df['Site']==feature['properties']['name_en']]['Unrest'].values[0]
            feature['properties']['tooltip'] = html.Div([
                                                html.Span(f"Site: {feature['id']}"), html.Br(),
                                                html.Span(f"Last Checked by: None"), html.Br(),
                                                html.Span(f"Most Recent SLC: None"), html.Br(),
                                                html.Span("Unrest Observed: "),
                                                html.Span(f"{unrest_bool}",
                                                          style={'color': 'red' if unrest_bool else 'green'})]) 
            # feature['properties']['icon'] = 'assets/greenVolcano.png'
    except requests.exceptions.ConnectionError:
        response_geojson = None
        # pass
    return response_geojson


def get_latest_quakes_chis_fsdn():
    """Query the CHIS fsdn for latest earthquakes"""
    url = 'https://earthquakescanada.nrcan.gc.ca/fdsnws/event/1/query'

    # Parameters for the query
    params = {
        'format': 'text',
        'starttime': (datetime.datetime.today() - datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
        'endtime': datetime.datetime.today().strftime('%Y-%m-%d'),
        'eventtype': 'earthquake',
    }
    
    # Make the request
    try:
        response = requests.get(url,
                                params=params,
                                timeout=10)
        if response.status_code == 200:
            # Parse the response text to a dataframe
            df = pd.read_csv(StringIO(response.text),
                             delimiter='|')
            # Create marker colour code based on event age
            df['Time_Delta'] = pd.to_datetime(
                df['Time'])-datetime.datetime.now(datetime.timezone.utc)
            df['Time_Delta'] = pd.to_numeric(-df['Time_Delta'].dt.days,
                                             downcast='integer')
            conditions = [
                (df['Time_Delta'] <= 2),
                (df['Time_Delta'] > 2) & (df['Time_Delta'] <= 7),
                (df['Time_Delta'] > 7) & (df['Time_Delta'] <= 31),
                (df['Time_Delta'] > 31)
                ]
            values = ['red', 'orange', 'yellow', 'white']
            df['quake_colour'] = np.select(conditions, values)
            df.sort_values(by='#EventID')
    except requests.exceptions.ConnectionError:
        df = pd.DataFrame()
        df['#EventID'] = None
    return df


def build_summary_table(targets_geojson):
    targets_df = pd.json_normalize(targets_geojson, record_path = ['features'])
    targets_df = targets_df[targets_df['id'].str.contains('^A|Edgecumbe')]
    targets_df['latest SAR Image Date'] = None
    targets_df = targets_df.rename(columns={'properties.name_en': 'Site'})
    unrest_table_df = pd.read_csv('app/Data/unrest_table.csv')
    # targets_df['Unrest'] = None
    targets_df = pd.merge(targets_df, unrest_table_df, on='Site', how='left')
    for site in targets_df['id']:
        site_index = targets_df.loc[targets_df['id']==site].index[0]
        try:
            response = requests.get(f"http://{config.get('API', 'vrrc_api_ip')}/targets/{site}")
            response_geojson = json.loads(response.content)
            if type(response_geojson['last_slc_datetime']) == str:
                targets_df.loc[site_index, 'latest SAR Image Date'] = response_geojson['last_slc_datetime'][0:10]
        except requests.exceptions.ConnectionError:
            targets_df.loc[site_index, 'latest SAR Image Date'] = None
    targets_df = targets_df.sort_values('id')
    return targets_df[['Site', 'latest SAR Image Date', 'Unrest']]


def get_green_volcanoes():
    """Return a list of green volcano points"""
    green_point_features = []
    green_icon = dict(
        iconUrl=dash.get_asset_url('green_volcano_transparent.png'),
        iconSize=[25, 25],
    )
    for feature in targets_geojson['features']:
        if feature['id'].startswith('A'):
            if (feature['geometry']['type'] == 'Point' and
                summary_table_df.loc[
                    summary_table_df['Site'] == feature['properties']['name_en']
                    ]['Unrest'].values[0] == False):
                green_point_features.append(feature)
    green_markers = [
        Marker(position=[point['geometry']['coordinates'][1],
                         point['geometry']['coordinates'][0]],
               icon=green_icon,
               children=Tooltip(html.P(point['properties']['tooltip'])),
               id=f"marker_{point['properties']['name_en']}"
               )
        for point in green_point_features
    ]
    return green_markers


def get_red_volcanoes():
    """Return a list of red volcano points"""
    red_point_features = []
    red_icon = dict(
        iconUrl=dash.get_asset_url('red_volcano_transparent.png'),
        iconSize=[25, 25],
    )
    for feat in targets_geojson['features']:
        if feat['id'].startswith('A') or feat['id'] == 'Edgecumbe':
            if (feat['geometry']['type'] == 'Point' and
                summary_table_df.loc[
                    summary_table_df['Site'] == feat['properties']['name_en']
                    ]['Unrest'].values[0] == True):
                red_point_features.append(feat)
    red_markers = [
        Marker(position=[point['geometry']['coordinates'][1],
                         point['geometry']['coordinates'][0]],
               icon=red_icon,
               children=Tooltip(html.P(point['properties']['tooltip'])),
               id=f"marker_{point['properties']['name_en']}"
               )
        for point in red_point_features
    ]
    return red_markers


config = get_config_params('scripts/config.ini')
targets_geojson = read_targets_geojson()
summary_table_df = build_summary_table(targets_geojson)


markers_red = get_red_volcanoes()
markers_green = get_green_volcanoes()
epicenters_df = get_latest_quakes_chis_fsdn()
on_each_feature = assign("""function(feature, layer, context){
    layer.bindTooltip(`${feature.properties.name_en}`)
}""")

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
        id='overview_map',
        style={'width': '100%', 'height': '100vh', 'position': 'relative'},
        children=[
            Map(
                id='map',
                style={'width': '100%', 'height': '95vh'},
                center=[54.64, -123.60],
                zoom=6,
                children=[

                    # TileLayer(),
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
                    *markers_green,
                    *markers_red,
                    *[
                        CircleMarker(
                            center=[row['Latitude'], row['Longitude']],
                            radius=3*row['Magnitude'],
                            fillColor=row['quake_colour'],
                            fillOpacity=0.6,
                            color='black',
                            weight=1,
                            # fill_colou='red',
                            # fill_opacity=0.6,
                            children=Popup(html.P([f"""Magnitude: \
                                                    {row['Magnitude']} \
                                                    {row['MagType']}""",
                                                   html.Br(),
                                                   f"Date: {row['Time'][0:10]}", html.Br(),
                                               f"Depth: {row['Depth/km']} km", html.Br(),
                                               f"EventID: {row['#EventID']}", html.Br(),
                                            ])),
                        )
                        for index, row in epicenters_df.sort_values(by='#EventID').iterrows() 
                    ]
                ]
            ),
        ]
    ),
    html.Div(
        id='table-container',
        style={'position': 'absolute',
               'top': '125px',
               'right': '250px',
               'width': '200px',
               'zIndex': 1000},
        children=[
            dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in summary_table_df.columns],
                data=summary_table_df.to_dict('records'),
                style_table={'color': 'black'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'Unrest', 'row_index': i},
                        'color': 'red' if unrest else 'green',
                    } for i, unrest in enumerate(summary_table_df['Unrest'])
                    # Add beam mode to latest slc date
                ],
            )
        ]
    ),
])


@callback(
    Output('url', 'pathname', allow_duplicate=True),
    [[Input(component_id=i.id, component_property='n_clicks') for i in markers_green],
     [Input(component_id=i.id, component_property='n_clicks') for i in markers_red]],
     prevent_initial_call=True,
     suppress_callback_exceptions=True
)
def navigate_to_site_page(*args):
    ctx = dash.callback_context
    print(type(ctx))
    return '/site'

# @callback(
#     Output(component_id='site-dropdown', component_property='value', allow_duplicate=True),
#     [[Input(component_id=i.id, component_property='n_clicks') for i in markers_green],
#      [Input(component_id=i.id, component_property='n_clicks') for i in markers_red]],
#      prevent_initial_call=True,
#      suppress_callback_exceptions=True
# )
# def select_new_site(target_id):
#     target_id = target_id.split('_', 1)[1]
#     return 
