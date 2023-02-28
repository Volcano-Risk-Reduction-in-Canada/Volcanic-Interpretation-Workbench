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

TITLE = 'Volcano InSAR Interpretation Workbench'
LOGO = 'Seal_of_the_Geological_Survey_of_Canada.png'

BASEMAP_URL = (
    'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer'
    '/tile/{z}/{y}/{x}')
BASEMAP_ATTRIBUTION = (
    'Tiles courtesy of the '
    '<a href="https://usgs.gov/">U.S. Geological Survey</a>')
BASEMAP_NAME = 'USGS Topo'

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


def extract_data(coherence_df):
    """Extract data for plotting."""
    all_dates = coherence_df['Reference Date'].unique()
    pair_dates = coherence_df['Pair Date'].unique()
    data = np.rot90(np.fliplr(coherence_df['Average Coherence'].to_numpy()
                              .reshape(len(all_dates), len(pair_dates))))

    return data, all_dates, pair_dates


def _valid_dates(coherence_df):
    return coherence_df['Reference Date'].dropna().unique()


def _coherence_csv(target_id):
    site, beam = target_id.split('_', 1)
    return f'Data/{site}/{beam}/CoherenceMatrix.csv'


# Construct dashboard
coherence = pd.read_csv(_coherence_csv(INITIAL_TARGET))
initial_data, initial_ref, initial_pair = extract_data(coherence)

fig = px.imshow(
    initial_data, x=initial_ref, y=initial_pair,
    color_continuous_scale='RdBu_r')
fig.update_yaxes(autorange=True)

app.layout = html.Div(
    id='parent',
    children=[
        html.H1(
            children=TITLE,
            style={
                'textAlign': 'center',
                'marginTop': 5,
                'marginBottom': 5,
            }),

        html.Div(
            children=[
                html.Label('Target_Beam:'),
                dcc.Dropdown(
                    id='site-dropdown',
                    options=list(TARGET_CENTRES.keys()),
                    value=INITIAL_TARGET,
                    style={'color': 'black'})],
            style={
                'width': 200,
                'marginLeft': '2%',
                'marginTop': 5,
                'marginBottom': 5,
            }),

        html.Div(
            children=[
                dl.Map([
                    dl.TileLayer(),
                    dl.LayersControl(
                        dl.BaseLayer(
                            dl.TileLayer(
                                url=BASEMAP_URL,
                                attribution=BASEMAP_ATTRIBUTION
                            ),
                            name=BASEMAP_NAME,
                            checked=True
                        ),
                    ),
                    dl.WMSTileLayer(
                        id='interferogram',
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
                    id='interferogram-bg',
                    center=TARGET_CENTRES[INITIAL_TARGET],
                    zoom=12,
                    style={
                        'height': '70%',
                    }),
                dcc.Graph(
                    id='date-graph',
                    figure=fig,
                    style={
                        'height': '30%',
                    }),
            ],
            style={
                'height': '800px',
                'width': '96%',
                'marginLeft': '2%',
            }
        ),
        # html.Div(),

        # html.Div(style={'width': '5%', 'display': 'inline-block'}),
        # html.Div(
        #     dl.Map([
        #         dl.TileLayer(),
        #         dl.LayersControl(
        #             dl.BaseLayer(
        #                 dl.TileLayer(
        #                     url=BASEMAP_URL,
        #                     attribution=BASEMAP_ATTRIBUTION
        #                 ),
        #                 name=BASEMAP_NAME,
        #                 checked=True
        #             ),
        #         ),
        #         dl.WMSTileLayer(
        #             id='intensity-map',
        #             url=f'{GEOSERVER_ENDPOINT}/{INITIAL_TARGET}/wms?',
        #             layers="cite:20210114_HH.rmli.geo.db",
        #             format="image/png",
        #             transparent=True,
        #             opacity=1.0),
        #         ],
        #         id='intensity-background',
        #         center=[50.64, -123.6],
        #         zoom=12,
        #     ),
        #     style={
        #         'width': '90%',
        #         'height': '550px',
        #         'display': 'inline-block'}
        #     ),
        # html.Div([
        #     dcc.Slider(
        #         min=0,
        #         max=len(_valid_dates(coherence)),
        #         step=1,
        #         marks={
        #             i: _valid_dates(coherence)[i] for i in range(
        #                 0, len(_valid_dates(coherence)), 10)},
        #         value=0,
        #         id='date-slider'),
        #     html.Div(id='date-display')
        # ]),
        # html.Div(),
    ]
)


@app.callback(
    Output(component_id='interferogram', component_property='layers'),
    Input(component_id='date-graph', component_property='clickData'))
def update_interferogram(click_data):
    """Update interferogram display."""
    if not click_data:
        return 'cite:20210717_HH_20210903_HH.adf.wrp.geo'
    x_date = json.dumps(click_data['points'][0]['x'], indent=2)
    y_date = json.dumps(click_data['points'][0]['y'], indent=2)

    dates = f'{x_date}_HH_{y_date}_HH'
    dates = dates.replace('-', '').replace('"', '')
    layers = f'cite:{dates}.adf.wrp.geo'
    print(f'Updating interferogram: {layers}')
    return layers


@app.callback(
    Output(component_id='interferogram', component_property='url'),
    Input(component_id='site-dropdown', component_property='value'))
def update_site(value):
    """Switch between sites."""
    url = f"{GEOSERVER_ENDPOINT}/{value}/wms?"
    print(f'New site url: {url}')
    return url


@app.callback(
    Output(component_id='date-graph', component_property='figure'),
    Input(component_id='site-dropdown', component_property='value'))
def update_coherence(target_id):
    """Display new coherence matrix."""
    # FIXME: See https://dash.plotly.com/sharing-data-between-callbacks.
    coherence_csv = _coherence_csv(target_id)
    print(f'Loading: {coherence_csv}')
    coherence = pd.read_csv(coherence_csv)

    new_data, new_ref, new_pair = extract_data(coherence)

    new_fig = px.imshow(
        new_data, x=new_ref, y=new_pair,
        color_continuous_scale='RdBu_r')
    new_fig.update_yaxes(autorange=True)
    return new_fig


@app.callback(
    Output(component_id='interferogram-bg', component_property='center'),
    Input(component_id='site-dropdown', component_property='value'))
def recenter_map(target_id):
    """Center map on new site."""
    coords = TARGET_CENTRES[target_id]
    print(f'Recentering: {coords}')
    return coords


# @app.callback(
#     Output('date-display', 'children'),
#     Input('date-slider', 'value'))
# def update_output(value):
#     "Update backscatter date text."
#     date = _valid_dates(coherence)[value]
#     title = f'Date: "{date}"'
#     print(f'Slider title: {title}')
#     return title


# @app.callback(
#     Output('intensity-map', 'layers'),
#     Input('date-slider', 'value'))
# def update_intensity(value):
#     "Update backscatter image on map"
#     date = _valid_dates(coherence)[value]
#     date = date.replace('-', '')
#     layers = f'cite:{date}_HH.rmli.geo.db'
#     print(f'Updating backscatter: {layers}')
#     return layers


if __name__ == '__main__':
    # TODO login and set up - or at least test - port forwarding
    # See https://stackoverflow.com/questions/66222667/how-to-use-session-manager-plugin-command/70311671#70311671
    app.run_server(host='0.0.0.0', port=8050, debug=True)
