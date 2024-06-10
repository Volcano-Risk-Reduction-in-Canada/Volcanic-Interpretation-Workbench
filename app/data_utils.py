import configparser
import json
import datetime
from io import StringIO

import requests
import dash
from dash import html
from dash_leaflet import (Marker,
                          Tooltip)
import numpy as np
import pandas as pd

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
        vrrc_api_ip = config.get('API', 'vrrc_api_ip')
        response = requests.get(f'http://{vrrc_api_ip}/targets/geojson/',
                                timeout=10)
        response_geojson = json.loads(response.content)
        unrest_table_df = pd.read_csv('app/Data/unrest_table.csv')
        calculate_and_append_centroids(response_geojson)
        for feature in response_geojson['features']:
            if unrest_table_df.loc[unrest_table_df['Site'] ==
                                   feature['properties']['name_en']
                                   ]['Unrest'].values.size > 0:
                unrest_bool = unrest_table_df.loc[
                    unrest_table_df['Site'] == feature['properties']['name_en']
                    ]['Unrest'].values[0]
            feature['properties']['tooltip'] = html.Div([
                html.Span(f"Site: {feature['id']}"), html.Br(),
                html.Span("Last Checked by: None"), html.Br(),
                html.Span("Most Recent SLC: None"), html.Br(),
                html.Span("Unrest Observed: "),
                html.Span(f"{unrest_bool}",
                          style={
                              'color': 'red' if unrest_bool else 'green'})])
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
        'starttime': (datetime.datetime.today() -
                      datetime.timedelta(
                          days=365)).strftime('%Y-%m-%d'),
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


def build_summary_table(targs_geojson):
    """Build a summary table with volcanoes and info on their unrest"""
    try:
        targets_df = pd.json_normalize(targs_geojson,
                                       record_path=['features'])
        targets_df = targets_df[targets_df['id'].str.contains('^A|Edgecumbe')]
        targets_df['latest SAR Image Date'] = None
        targets_df = targets_df.rename(columns={'properties.name_en': 'Site'})
        unrest_table_df = pd.read_csv('app/Data/unrest_table.csv')
        # targets_df['Unrest'] = None
        targets_df = pd.merge(targets_df,
                              unrest_table_df,
                              on='Site',
                              how='left')
        for site in targets_df['id']:
            site_index = targets_df.loc[targets_df['id'] == site].index[0]
            try:
                url = config.get('API', 'vrrc_api_ip')
                response = requests.get(
                    f"http://{url}/targets/{site}",
                    timeout=10)
                response_geojson = json.loads(response.content)
                if type(response_geojson['last_slc_datetime']) is str:
                    last_slc_date = response_geojson['last_slc_datetime'][0:10]
                    targets_df.loc[site_index,
                                   'latest SAR Image Date'
                                   ] = last_slc_date
            except requests.exceptions.ConnectionError:
                targets_df.loc[site_index, 'latest SAR Image Date'] = None
        targets_df = targets_df.sort_values('id')
    except NotImplementedError:
        targets_df = pd.DataFrame(columns=['Site',
                                           'latest SAR Image Date',
                                           'Unrest'])
        targets_df.loc[0] = ["API Connection Error"] * 3
    return targets_df[['Site', 'latest SAR Image Date', 'Unrest']]


def get_green_volcanoes():
    """Return a list of green volcano points"""
    print("GET green volc")
    try:
        green_point_features = []
        green_icon = dict(
            iconUrl=dash.get_asset_url('green_volcano_transparent.png'),
            iconSize=[25, 25],
        )
        for feature in targets_geojson['features']:
            if feature['id'].startswith('A'):
                if (feature['geometry']['type'] == 'Point' and
                    not summary_table_df.loc[
                            summary_table_df[
                                'Site'] == feature['properties']['name_en']
                            ]['Unrest'].values[0]):
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
    except TypeError:
        green_markers = [Marker(position=[0., 0.],
                                icon=green_icon,
                                children=Tooltip("API Error"),
                                id="TypeError_green")]
    return green_markers


def get_red_volcanoes():
    """Return a list of red volcano points"""
    print("GET red volc")
    try:
        red_point_features = []
        red_icon = dict(
            iconUrl=dash.get_asset_url('red_volcano_transparent.png'),
            iconSize=[25, 25],
        )
        for feature in targets_geojson['features']:
            if feature['id'].startswith('A') or feature['id'] == 'Edgecumbe':
                if (feature['geometry']['type'] == 'Point' and
                    summary_table_df.loc[
                        summary_table_df[
                            'Site'] == feature['properties']['name_en']
                        ]['Unrest'].values[0]):
                    red_point_features.append(feature)
        red_markers = [
            Marker(position=[point['geometry']['coordinates'][1],
                             point['geometry']['coordinates'][0]],
                   icon=red_icon,
                   children=Tooltip(html.P(point['properties']['tooltip'])),
                   id=f"marker_{point['properties']['name_en']}"
                   )
            for point in red_point_features
        ]
    except TypeError:
        red_markers = [Marker(position=[0., 0.],
                              icon=red_icon,
                              children=Tooltip("API Error"),
                              id="TypeError_red")]
    return red_markers


config = get_config_params('config.ini')
targets_geojson = read_targets_geojson()
summary_table_df = build_summary_table(targets_geojson)