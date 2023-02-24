#!/usr/bin/python3
# =================================================================
# SPDX-License-Identifier: MIT
#
# Copyright (C) 2021-2022 Government of Canada
#
# Main Authors: Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
#
# =================================================================


from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
import dash_leaflet as dl

import plotly.express as px

import configparser
import json
import numpy as np
import pandas as pd


def get_config_params(args):
    """
    Parse Input/Output columns from supplied *.ini file
    """
    configParseObj = configparser.ConfigParser()
    configParseObj.read(args)
    return configParseObj


config = get_config_params("config.ini")

# This loads the "darkly" themed figure template from dash-bootstrap-templates
#  library, adds it to plotly.io and makes it the default figure template.
load_figure_template("darkly")

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

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

# Coherence Pair Data
dfCohFull = pd.read_csv('Data/Meager/5M3/CoherenceMatrix.csv')

fig = px.imshow(np.rot90(np.fliplr(dfCohFull['Average Coherence'].to_numpy().reshape(len(dfCohFull['Reference Date'].unique()),
                                                                                     len(dfCohFull['Reference Date'].unique())))),
                x=dfCohFull['Reference Date'].unique(),
                y=dfCohFull['Pair Date'].unique(),
                color_continuous_scale='RdBu_r'
                )
fig.update_yaxes(autorange=True)

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
        dl.Map([dl.TileLayer(),
                dl.LayersControl(
                    dl.BaseLayer(
                            dl.TileLayer(
                                # Basemaps
                                url='https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
                                attribution='Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>'
                            ),
                            name="USGS Topo",
                            checked=True
                            ),
                        ),
                dl.WMSTileLayer(id='map',
                                url=f"{config.get('geoserver', 'geoserverEndpoint')}/{workspace}/wms?",
                                layers="cite:20210717_HH_20210903_HH.adf.wrp.geo",
                                format="image/png",
                                transparent=True,
                                opacity=0.75),
                dl.WMSTileLayer(url=f"{config.get('geoserver', 'geoserverEndpoint')}/vectorLayers/wms?",
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

    # html.Div(),

    # html.Div(style={'width': '5%', 'display': 'inline-block'}),
    # html.Div(
    #     dl.Map([dl.TileLayer(),
    #             dl.LayersControl(
    #                 dl.BaseLayer(
    #                         dl.TileLayer(
    #                             # Selection of Basemaps
    #                             url='https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
    #                             attribution='Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>'
    #                         ),
    #                         name="USGS Topo",
    #                         checked=True
    #                         ),
    #                     ),
    #             dl.WMSTileLayer(id='rmlimap',
    #                             url=f"{config.get('geoserver', 'geoserverEndpoint')}/Meager_5M3/wms?",
    #                             layers="cite:20210114_HH.rmli.geo.db",
    #                             format="image/png",
    #                             transparent=True,
    #                             opacity=1.0),
    #                 ],
    #            id='leafletMapRMLI',
    #            center=[50.64, -123.6],
    #            zoom=12
    #            ),
    #     style={'width': '90%', 'height': '550px', 'display': 'inline-block'}
    #     ),
    # html.Div([
    #     dcc.Slider(min=0,
    #                max=len(dfCohFull.dropna()['Reference Date'].unique()),
    #                step=1,
    #                marks={i: dfCohFull.dropna()['Reference Date'].unique()[i] for i in range(0, len(dfCohFull.dropna()['Reference Date'].unique()), 10)},
    #                value=0,
    #                id='my-slider'
    #                ),
    #     html.Div(id='slider-output-container')
    #         ]),
    # html.Div(),
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
def updateSite(value):
    dfCohFull = pd.read_csv('Data/{}/{}/CoherenceMatrix.csv'.format('_'.join(value.split('_')[:-1]), value.split('_')[-1]))

    fig = px.imshow(np.rot90(np.fliplr(dfCohFull['Average Coherence'].to_numpy().reshape(len(dfCohFull['Reference Date'].unique()),len(dfCohFull['Reference Date'].unique())))),
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
def update_output(value):
    date = dfCohFull.dropna()['Reference Date'].unique()[value].replace('-',
                                                                        '')
    print('cite:{}_HH.rmli.geo.db'.format(date))
    return 'cite:{}_HH.rmli.geo.db'.format(date)


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
