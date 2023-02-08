#!/usr/bin/python3
# =================================================================
# SPDX-License-Identifier: MIT
#
# Copyright (C) 2021-2022 Government of Canada
#
# Main Authors: Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
#
# =================================================================


import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl

import plotly.express as px
import plotly.graph_objects as go

import configparser
import json
import numpy as np
import pandas as pd

from dash.dependencies import Input, Output
from dash_bootstrap_templates import load_figure_template


def get_config_params(args):
    """
    Parse Input/Output columns from supplied *.ini file
    """
    configParseObj = configparser.ConfigParser()
    configParseObj.read(args)
    return configParseObj


config = get_config_params("config.ini")
geoserverEndpoint = config.get('geoserver', 'geoserverEndpoint')

# This loads the "darkly" themed figure template from dash-bootstrap-templates
#  library, adds it to plotly.io and makes it the default figure template.
load_figure_template("darkly")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

workspace = "Meager_5M3"
stackList = ['Meager_5M2',
             'Meager_5M3',
             'Meager_5M8',
             'Meager_5M10',
             'Meager_5M15',
             'Meager_5M21',
             'Garibaldi_3M6',
             'Garibaldi_3M7',
             'Garibaldi_3M18',
             'Garibaldi_3M23',
             'Garibaldi_3M30',
             'Garibaldi_3M34',
             'Garibaldi_3M42',
             'Cayley_3M1',
             'Cayley_3M6',
             'Cayley_3M13',
             'Cayley_3M14',
             'Cayley_3M17',
             'Cayley_3M24',
             'Cayley_3M30',
             'Cayley_3M36',
             'Edgecumbe_3M36D',
             'Edziza_North_3M13',
             'Edziza_North_3M41',
             'Edziza_South_3M12',
             'Edziza_South_3M31',
             'Edziza_South_3M42',
             'Tseax_3M7',
             'Tseax_3M9',
             'Tseax_ 3M19',
             'Tseax_3M40',
             'Nazko_3M9',
             'Nazko_3M20',
             'Nazko_3M31',
             'Hoodoo_3M8',
             'Hoodoo_3M11',
             'Hoodoo_3M14',
             'Hoodoo_3M38',
             'Hoodoo_3M41',
             'LavaFork_3M11',
             'LavaFork_3M20',
             'LavaFork_3M21',
             'LavaFork_3M29',
             'LavaFork_3M31',
             'LavaFork_3M41']

siteDict = {'Meager_5M2': [50.64, -123.60],
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
            'Edgecumbe_3M36D': [57.05, -135.75],
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
            'LavaFork_3M41': [56.42, -130.85]}

# Coherence Pair Data
dfCohFull = pd.read_csv('Data/Meager/5M3/CoherenceMatrix.csv')

cohImgSize = len(dfCohFull['Reference Date'].unique())
cohImg = dfCohFull['Average Coherence'].to_numpy().reshape(cohImgSize,
                                                           cohImgSize)
cohImg = np.rot90(np.fliplr(cohImg))

fig = px.imshow(cohImg,
                x=dfCohFull['Reference Date'].unique(),
                y=dfCohFull['Pair Date'].unique(),
                color_continuous_scale='RdBu_r'
                )
fig.update_yaxes(autorange=True)

# Baseline Pair Data
dfBaseline = pd.read_csv('Data/Meager/5M3/bperp_file_all',
                         delim_whitespace=True,
                         header=None,
                         names=['Reference Date',
                                'Pair Date',
                                'bperp',
                                'btemp',
                                'bperp2',
                                'NA'])
dfBaseline['Reference Date'] = pd.to_datetime(dfBaseline['Reference Date'],
                                              format="%Y%m%d")
dfBaseline['Pair Date'] = pd.to_datetime(dfBaseline['Pair Date'],
                                         format="%Y%m%d")
bperpScatterfig = go.Scatter(x=dfBaseline['Pair Date'],
                             y=dfBaseline['bperp'],
                             mode='markers')

dfBaseLineEdge = dfCohFull[dfCohFull['Average Coherence'].notna()]
dfBaseLineEdge = dfBaseLineEdge.drop(columns=['Average Coherence'])
dfBaseLineEdge['Reference Date'] = \
    pd.to_datetime(dfBaseLineEdge['Reference Date'],
                   format="%Y-%m-%d")

dfBaseLineEdge['Pair Date'] = \
    pd.to_datetime(dfBaseLineEdge['Pair Date'],
                   format="%Y-%m-%d")

dfBaseLineEdge = pd.merge(dfBaseLineEdge,
                          dfBaseline[['Pair Date', 'bperp']],
                          right_on='Pair Date',
                          left_on='Reference Date',
                          how='left')
dfBaseLineEdge = dfBaseLineEdge.drop(columns=['Pair Date_y'])
dfBaseLineEdge = \
    dfBaseLineEdge.rename(columns={"Pair Date_x": "Pair Date",
                                   "bperp": "bperp_reference_date"})
dfBaseLineEdge = pd.merge(dfBaseLineEdge,
                          dfBaseline[['Pair Date', 'bperp']],
                          right_on='Pair Date',
                          left_on='Pair Date',
                          how='left')

dfBaseLineEdge = dfBaseLineEdge.rename(columns={"bperp": "bperp_pair_date"})
dfBaseLineEdge = dfBaseLineEdge[dfBaseLineEdge['bperp_reference_date'].notna()]

edge_x = []
edge_y = []

for idx, edge in dfBaseLineEdge.iterrows():
    edge_x.append(edge['Reference Date'])
    edge_x.append(edge['Pair Date'])
    edge_y.append(edge['bperp_reference_date'])
    edge_y.append(edge['bperp_pair_date'])

bperpLinefig = go.Scatter(x=edge_x, y=edge_y,
                          line=dict(width=0.5, color='#888'),
                          mode='lines')

bperpCombinedFig = go.Figure(data=[bperpLinefig, bperpScatterfig])
bperpCombinedFig.update_layout(yaxis_title="Perpendicular Baseline (m)")
bperpCombinedFig.update(layout_showlegend=False)


app.layout = html.Div(id='parent', children=[
    html.Div(style={'width': '5%', 'display': 'inline-block'}),
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
        dcc.Dropdown(stackList, stackList[1], id='site-dropdown'),
        style={'width': '35%',
               'display': 'inline-block',
               'color': 'black'}),

    html.Div(style={'width': '5%',
                    'display': 'inline-block'}),

    html.Div([
        dcc.Graph(id='graph', figure=fig,
                  style={'position': 'absolute',
                         'width': '25%',
                         'height': '45%',
                         'margin-left': '69.5%',
                         'margin-top': '0.5%',
                         'zIndex': 2}
                  ),
        dcc.Graph(id='baseline_plot',
                  figure=bperpCombinedFig,
                  style={'position': 'absolute',
                         'width': '25%',
                         'height': '45%',
                         'margin-left': '69.5%',
                         'margin-top': '27%',
                         'zIndex': 2}),
        dl.Map([dl.TileLayer(),
                dl.LayersControl(
                    dl.BaseLayer(
                            dl.TileLayer(
                                # Basemaps
                                url=("https://basemap.nationalmap.gov/arcgis/"
                                     "rest/services/USGSTopo/MapServer/tile/"
                                     "{z}/{y}/{x}"),
                                attribution=("Tiles courtesy of the "
                                             "<a href='https://usgs.gov/'>"
                                             "U.S. Geological Survey</a>")
                            ),
                            name="USGS Topo",
                            checked=True
                            ),
                        ),
                dl.WMSTileLayer(id='map',
                                url=f"{geoserverEndpoint}/{workspace}/wms?",
                                layers=("cite:"
                                        "20210717_HH_20210903_HH.adf.wrp.geo"),
                                format="image/png",
                                transparent=True,
                                opacity=0.75),
                dl.WMSTileLayer(url=f"({geoserverEndpoint}/vectorLayers/wms?",
                                layers="cite:permanent_snow_and_ice_2",
                                format="image/png",
                                transparent=True,
                                opacity=1.0),
                ],
               id='leafletMap',
               center=[50.64, -123.6],
               zoom=12,
               style={'position': 'absolute',
                      'width': '90%',
                      'height': '900px',
                      'margin-left': '5%',
                      'zIndex': 1}
               )],
             style={'width': '90%',
                    'height': '900px',
                    'left-margin': '5%'}
             ),
    ])


# Update interferogram selection displayed on leaflet map
@app.callback(
    Output(component_id="map", component_property="layers"),
    Input(component_id="graph", component_property="clickData"))
def update_datepair(clickData):
    if not clickData:
        return 'cite:20210717_HH_20210903_HH.adf.wrp.geo'
    dates = '{}_HH_{}_HH'.format(json.dumps(clickData['points'][0]['x'],
                                            indent=2),
                                 json.dumps(clickData['points'][0]['y'],
                                            indent=2))
    dates = dates.replace('-', '').replace('"', '')
    print(dates)
    return 'cite:{}.adf.wrp.geo'.format(dates)


# Switch between Volcano Sites
@app.callback(
    Output(component_id="map", component_property="url"),
    Input(component_id="site-dropdown", component_property="value"))
def updateSite(value):
    return f"{config.get('geoserver', 'geoserverEndpoint')}/{value}/wms?"


# Display new Coherence Matrix
@app.callback(
    Output(component_id="graph", component_property="figure"),
    Input(component_id="site-dropdown", component_property="value"))
def updateSiteCohMatrix(value):
    site = '_'.join(value.split('_')[:-1])
    beam = value.split('_')[-1]
    dfCohFull = pd.read_csv(f'Data/{site}/{beam}/CoherenceMatrix.csv')

    cohImgSize = len(dfCohFull['Reference Date'].unique())
    cohImg = dfCohFull['Average Coherence'].to_numpy().reshape(cohImgSize,
                                                               cohImgSize)
    cohImg = np.rot90(np.fliplr(cohImg))

    fig = px.imshow(cohImg,
                    x=dfCohFull['Reference Date'].unique(),
                    y=dfCohFull['Pair Date'].unique(),
                    color_continuous_scale='RdBu_r'
                    )
    fig.update_yaxes(autorange=True)
    return fig


# Center Leaflet map on new volcano site
@app.callback(
    Output(component_id="leafletMap", component_property="center"),
    Input(component_id="site-dropdown", component_property="value"))
def updateCenter(value):
    centerDict = {'Meager_5M2': [50.64, -123.60],
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
                  'LavaFork_3M41': [56.42, -130.85]}
    print(centerDict[value])
    return centerDict[value]


# Update backscatter date text from slider
@app.callback(
    Output('slider-output-container', 'children'),
    Input('my-slider', 'value'))
def update_output(value):
    selectedDate = dfCohFull.dropna()['Reference Date'].unique()[value]
    return f'Date: "{selectedDate}"'


# Update Backscatter image on leaflet map
@app.callback(
    Output('rmlimap', 'layers'),
    Input('my-slider', 'value'))
def update_backscatterMap(value):
    date = dfCohFull.dropna()['Reference Date'].unique()[value].replace('-',
                                                                        '')
    print('cite:{}_HH.rmli.geo.db'.format(date))
    return 'cite:{}_HH.rmli.geo.db'.format(date)


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
