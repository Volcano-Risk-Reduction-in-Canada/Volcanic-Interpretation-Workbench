#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
  - Nick Ackerley <nicholas.ackerley@nrcan-rncan.gc.ca>
"""
import json
import configparser

import numpy as np
import pandas as pd

from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import plotly.express as px


def get_config_params(args):
    """Parse configuration from supplied file."""
    config_obj = configparser.ConfigParser()
    config_obj.read(args)
    return config_obj


config = get_config_params("config.ini")
GEOSERVER_ENDPOINT = config.get('geoserver', 'geoserverEndpoint')

load_figure_template('darkly')
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

BASEMAP_URL = (
    'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer'
    '/tile/{z}/{y}/{x}')
BASEMAP_ATTRIBUTION = (
    'Tiles courtesy of the '
    '<a href="https://usgs.gov/">U.S. Geological Survey</a>')

INITIAL_TARGET = 'Meager_5M3'
TARGET_CENTRES = {
    'Meager_5M2': [50.64, -123.60],
    'Meager_5M3': [50.64, -123.60],
    'Meager_5M8': [50.64, -123.60],
    'Meager_5M10': [50.64, -123.60],
    'Meager_5M15': [50.64, -123.60],
    'Meager_5M21': [50.64, -123.60],
    'Garibaldi_3M6': [49.90, -122.99],
    'Garibaldi_3M7': [49.90, -122.99],
    'Garibaldi_3M18': [49.90, -122.99],
    'Garibaldi_3M23': [49.90, -122.99],
    'Garibaldi_3M30': [49.90, -122.99],
    'Garibaldi_3M34': [49.90, -122.99],
    'Garibaldi_3M42': [49.90, -122.99],
    'Cayley': [50.12, -123.29],
    'Cayley_3M1': [50.12, -123.29],
    'Cayley_3M6': [50.12, -123.29],
    'Cayley_3M13': [50.12, -123.29],
    'Cayley_3M14': [50.12, -123.29],
    'Cayley_3M17': [50.12, -123.29],
    'Cayley_3M24': [50.12, -123.29],
    'Cayley_3M30': [50.12, -123.29],
    'Cayley_3M36': [50.12, -123.29],
    'Edgecumbe_3M36D': [50.05, -135.75],
    'Edziza_North_3M13': [57.74, -130.64],
    'Edziza_North_3M41': [57.74, -130.64],
    'Edziza_South_3M12': [57.64, -130.64],
    'Edziza_South_3M31': [57.64, -130.64],
    'Edziza_South_3M42': [57.64, -130.64],
    'Tseax_3M7': [55.11, -128.90],
    'Tseax_3M9': [55.11, -128.90],
    'Tseax_ 3M19': [55.11, -128.90],
    'Tseax_3M40': [55.11, -128.90],
    'Nazko_3M9': [52.93, -123.73],
    'Nazko_3M20': [52.93, -123.73],
    'Nazko_3M31': [52.93, -123.73],
    'Hoodoo_3M8': [56.77, -131.29],
    'Hoodoo_3M11': [56.77, -131.29],
    'Hoodoo_3M14': [56.77, -131.29],
    'Hoodoo_3M38': [56.77, -131.29],
    'Hoodoo_3M41': [56.77, -131.29],
    'LavaFork_3M11': [56.42, -130.85],
    'LavaFork_3M20': [56.42, -130.85],
    'LavaFork_3M21': [56.42, -130.85],
    'LavaFork_3M29': [56.42, -130.85],
    'LavaFork_3M31': [56.42, -130.85],
    'LavaFork_3M41': [56.42, -130.85],
}

# Coherence Pair Data
coherence = pd.read_csv('Data/Meager/5M3/CoherenceMatrix.csv')


def extract_data(coherence_df):
    """Extract data for plotting."""
    ref_dates = coherence_df['Reference Date'].unique()
    pair_dates = coherence_df['Pair Date'].unique()
    data = np.rot90(np.fliplr(coherence_df['Average Coherence'].to_numpy()
                              .reshape(len(ref_dates), len(pair_dates))))

    return data, ref_dates, pair_dates


initial_data, initial_ref, initial_pair = extract_data(coherence)

fig = px.imshow(
    initial_data, x=initial_ref, y=initial_pair,
    color_continuous_scale='RdBu_r')
fig.update_yaxes(autorange=True)

app.layout = html.Div(id='parent', children=[
    html.Div(style={'width': '5%', 'display': 'inline-block'}),
    # FIXME: This is not just a project of the GSC ...
    html.Img(src=app.get_asset_url(
                'Seal_of_the_Geological_Survey_of_Canada.png'),
             style={'width': '10%',
                    'display': 'inline-block'}),
    html.Div(style={'width': '5%',
                    'display': 'inline-block'}),
    html.H1(id='H1',
            children='Volcano InSAR Interpretation Workbench',
            style={'textAlign': 'center',
                   'marginTop': 40,
                   'marginBottom': 40,
                   'display': 'inline-block'}),
    html.Div(style={'height': '10px'}),
    html.Div(style={'width': '5%',
                    'display': 'inline-block'}),

    html.Div(
        dcc.Dropdown(list(TARGET_CENTRES.keys()), INITIAL_TARGET,
                     id='site-dropdown'),
        style={'width': '35%',
               'display': 'inline-block',
               'color': 'black'}),

    html.Div(style={'width': '5%',
                    'display': 'inline-block'}),

    html.Div([
        dcc.Graph(
            id='graph',
            figure=fig,
            style={
                'position': 'absolute',
                'width': '25%',
                'height': '45%',
                'margin-left': '69.5%',
                'margin-top': '0.5%',
                'zIndex': 2}),
        dl.Map([
            dl.TileLayer(),
            dl.LayersControl(
                dl.BaseLayer(
                    dl.TileLayer(
                        # Basemaps
                        url=BASEMAP_URL,
                        attribution=BASEMAP_ATTRIBUTION
                    ),
                    name='USGS Topo',
                    checked=True
                ),
            ),
            dl.WMSTileLayer(
                id='map',
                url=f"{GEOSERVER_ENDPOINT}/{INITIAL_TARGET}/wms?",
                layers='cite:20210717_HH_20210903_HH.adf.wrp.geo',
                format='image/png',
                transparent=True,
                opacity=0.75),
            dl.WMSTileLayer(
                url=f"{GEOSERVER_ENDPOINT}/vectorLayers/wms?",
                layers='cite:permanent_snow_and_ice_2',
                format='image/png',
                transparent=True,
                opacity=1.0)],
            id='leafletMap',
            center=[50.64, -123.6],
            zoom=12,
            style={
                'position': 'absolute',
                'width': '90%',
                'height': '900px',
                'margin-left': '5%',
                'zIndex': 1},
            )],
        style={
            'width': '90%',
            'height': '900px',
            'left-margin': '5%'}
    ),
])


@app.callback(
    Output(component_id='map', component_property='layers'),
    Input(component_id='graph', component_property='clickData'))
def update_interferogram(click_data):
    """Update interferogram selection displayed on leaflet map."""
    if not click_data:
        return 'cite:20210717_HH_20210903_HH.adf.wrp.geo'
    x_date = json.dumps(click_data['points'][0]['x'], indent=2)
    y_date = json.dumps(click_data['points'][0]['y'], indent=2)

    dates = f'{x_date}_HH_{y_date}_HH'
    dates = dates.replace('-', '').replace('"', '')
    print(dates)
    return f'cite:{dates}.adf.wrp.geo'


@app.callback(
    Output(component_id='map', component_property='url'),
    Input(component_id='site-dropdown', component_property='value'))
def update_site(value):
    """Switch between sites."""
    return f"{GEOSERVER_ENDPOINT}/{value}/wms?"


@app.callback(
    Output(component_id='graph', component_property='figure'),
    Input(component_id='site-dropdown', component_property='value'))
def update_coherence(value):
    """Display new coherence matrix."""
    site, beam = value.split('_', 1)
    # FIXME: See https://dash.plotly.com/sharing-data-between-callbacks.
    coherence = pd.read_csv(f'Data/{site}/{beam}/CoherenceMatrix.csv')

    new_data, new_ref, new_pair = extract_data(coherence)

    new_fig = px.imshow(
        new_data, x=new_ref, y=new_pair,
        color_continuous_scale='RdBu_r')
    new_fig.update_yaxes(autorange=True)
    return new_fig


@app.callback(
    Output(component_id='leafletMap', component_property='center'),
    Input(component_id='site-dropdown', component_property='value'))
def recenter_map(value):
    """Center map on new site."""
    coords = TARGET_CENTRES[value]
    print(coords)
    return coords


@app.callback(
    Output('slider-output-container', 'children'),
    Input('my-slider', 'value'))
def update_output(value):
    "Update backscatter date text."
    selected_date = coherence.dropna()['Reference Date'].unique()[value]
    return f'Date: "{selected_date}"'


@app.callback(
    Output('rmlimap', 'layers'),
    Input('my-slider', 'value'))
def update_image(value):
    "Update backscatter image on map"
    date = coherence.dropna()['Reference Date'].unique()[value]
    date = date.replace('-', '')
    result = f'cite:{date}_HH.rmli.geo.db'
    print(result)
    return result


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
