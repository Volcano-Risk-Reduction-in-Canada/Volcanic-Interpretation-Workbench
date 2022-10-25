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
import json
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output
import dash_leaflet as dl
import pandas as pd
import dash_bootstrap_components as dbc

import numpy as np

from dash_bootstrap_templates import load_figure_template

# This loads the "darkly" themed figure template from dash-bootstrap-templates library,
# adds it to plotly.io and makes it the default figure template.
load_figure_template("darkly")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
# app = dash.Dash(__name__)

# NorthSlide_3M14D
workspace="Meager_5M3"
# workspace="Garibaldi_3M23"
# workspace="Tseax_3M19"
stackList = ['Garibaldi_3M23', 'Meager_5M3', 'Meager_5M21','Cayley', 'Tseax_3M19', 'LavaFork_3M41']
siteDict={'Garibaldi_3M23':[49.90, -122.99],
                'Meager_5M3':[50.64, -123.60],
                'Meager_5M21':[50.64, -123.60],
                'Cayley':[50.12, -123.29],
                'Tseax_3M19':[55.11, -128.90],
                'LavaFork_3M41':[56.42, -130.85]}

#Dummy Coherence Pair Data
dfCohFull = pd.read_csv('Data/Meager/5M3/coherenceMatrix.csv')
# dfCohFull = pd.read_csv('Data/Garibaldi/3M23/CoherenceMatrix.csv')
# dfCohFull = pd.read_csv('Data/Tseax/3M19/CoherenceMatrix.csv')

fig = px.imshow(np.rot90(np.fliplr(dfCohFull['Average Coherence'].to_numpy().reshape(len(dfCohFull['Reference Date'].unique()),len(dfCohFull['Reference Date'].unique())))),
                 x=dfCohFull['Reference Date'].unique(),
                 y=dfCohFull['Pair Date'].unique(),
                 color_continuous_scale='RdBu_r'
                )
fig.update_yaxes(autorange=True) 


app.layout = html.Div(id = 'parent', children = [
    html.Div(style={'width': '5%','display': 'inline-block'}),
    html.Img(src=app.get_asset_url('Seal_of_the_Geological_Survey_of_Canada.png'),
                      style={'width': '10%','display': 'inline-block'}),
    html.Div(style={'width': '5%','display': 'inline-block'}),
    html.H1(id='H1',
            children='Volcano InSAR Interpretation Workbench',
            style = {'textAlign':'center', 'marginTop':40, 'marginBottom':40, 'display': 'inline-block'}),
    html.Div(style={'height': '10px'}),
    html.Div(style={'width': '5%','display': 'inline-block'}),

    html.Div(
        dcc.Dropdown(stackList, stackList[1], id='site-dropdown'),
            style={'width': '35%','display': 'inline-block', 'color': 'black'}),

    html.Div(),

    html.Div(style={'width': '5%','display': 'inline-block'}),

    html.Div(
        dcc.Graph(id='graph', figure=fig),
        style={'width': '35%', 'display': 'inline-block', 'height': '450px'}),

    html.Div(
        dl.Map([dl.TileLayer(), 
                dl.LayersControl(
                    dl.BaseLayer(
                            dl.TileLayer(
                                #Selection of Basemaps 
                                # url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                                # attribution="'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'",
                                # url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
                                # attribution="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community"
                                # url='https://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png?apikey=8967084505674fce9bee8be62e2ac7f1'
                                # url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}'
                                url='https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
                                attribution='Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>'
                                # url ='https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}'
                            ),
                            name="USGS Topo",
                            checked=True
                            ),
                        ),
                dl.WMSTileLayer(url="http://localhost:8080/geoserver/{}/wms?".format(workspace),
                                layers="cite:meager_bedem_subset_10N_hs",
                                format="image/png",
                                transparent=True,
                                opacity=1.0),
                dl.WMSTileLayer(id='map',
                                url="http://localhost:8080/geoserver/{}/wms?".format(workspace),
                                layers="cite:20210717_HH_20210903_HH.adf.wrp.geo",
                                format="image/png",
                                transparent=True,
                                opacity=0.75),
                    ],
                id='leafletMap',
                center=[50.64, -123.6],
                zoom=12
                ),
        style={'width': '55%','display': 'inline-block', 'height': '450px'}
        ),
    html.Div(),
    # html.Div(
    #     html.H1(id='output', children='Selected Site', style = {'textAlign':'center',\
    #                                         'marginTop':40,'marginBottom':40})
    #     ),
    html.Div(style={'width': '5%','display': 'inline-block'}),
    html.Div(
        dl.Map([dl.TileLayer(), 
                dl.LayersControl(
                    dl.BaseLayer(
                            dl.TileLayer(
                                #Selection of Basemaps 
                                url='https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
                                attribution='Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>'
                            ),
                            name="USGS Topo",
                            checked=True
                            ),
                        ),
                dl.WMSTileLayer(id='rmlimap',
                                url="http://localhost:8080/geoserver/{}/wms?".format("Meager_5M3"),
                                layers="cite:20210114_HH.rmli.geo.db",
                                format="image/png",
                                transparent=True,
                                opacity=1.0),
                    ],
                id='leafletMapRMLI',
                center=[50.64, -123.6],
                zoom=12
                ),
        style={'width': '90%', 'height': '550px', 'display': 'inline-block'}
        ),
    html.Div([
        dcc.Slider(min=0,
               max=len(dfCohFull.dropna()['Reference Date'].unique()),
               step=1,
               marks={i: dfCohFull.dropna()['Reference Date'].unique()[i] for i in range(0, len(dfCohFull.dropna()['Reference Date'].unique()), 10)},
            #    marks={i: dfCohFull['Reference Date'].unique()[i] for i in np.linspace(0, len(dfCohFull['Reference Date'].unique()), 10)},
               value=0,
               id='my-slider'
        ),
    html.Div(id='slider-output-container')
        ]),
    html.Div(),
    ])


@app.callback(
    # Output(component_id="output", component_property="children"),
    Output(component_id="map", component_property="layers"),
    Input(component_id="graph", component_property="clickData"))
def update_datepair(clickData):
    if not clickData:
        return 'cite:20210717_HH_20210903_HH.adf.wrp.geo'
    dates='{}_HH_{}_HH'.format(json.dumps(clickData['points'][0]['x'], indent=2),
                               json.dumps(clickData['points'][0]['y'], indent=2))
    dates = dates.replace('-','').replace('"','')
    print(dates)
    return'cite:{}.adf.wrp.geo'.format(dates)


@app.callback(
    # Output(component_id="output", component_property="children"),
    Output(component_id="map", component_property="url"),
    Input(component_id="site-dropdown", component_property="value"))
def updateSite(value):
    return "http://localhost:8080/geoserver/{}/wms?".format(value)


@app.callback(
    Output(component_id="graph", component_property="figure"),
    Input(component_id="site-dropdown", component_property="value"))
def updateSite(value):
    dfCohFull = pd.read_csv('Data/{}/{}/CoherenceMatrix.csv'.format(value.split('_')[0], value.split('_')[1]))

    fig = px.imshow(np.rot90(np.fliplr(dfCohFull['Average Coherence'].to_numpy().reshape(len(dfCohFull['Reference Date'].unique()),len(dfCohFull['Reference Date'].unique())))),
                    x=dfCohFull['Reference Date'].unique(),
                    y=dfCohFull['Pair Date'].unique(),
                    color_continuous_scale='RdBu_r'
                    )
    fig.update_yaxes(autorange=True) 
    return fig


@app.callback(
    Output(component_id="leafletMap", component_property="center"),
    Input(component_id="site-dropdown", component_property="value"))
def updateCenter(value):
    centerDict={'Garibaldi_3M23':[49.90, -122.99],
                'Meager_5M3':[50.64, -123.60],
                'Cayley':[50.12, -123.29],
                'Tseax_3M19':[55.11, -128.90],
                'LavaFork_3M41':[56.42, -130.85]}
    print(centerDict[value])
    return centerDict[value]


@app.callback(
    Output('slider-output-container', 'children'),
    Input('my-slider', 'value'))
def update_output(value):
    return 'Date: "{}"'.format(dfCohFull.dropna()['Reference Date'].unique()[value])

@app.callback(
    Output('rmlimap', 'layers'),
    Input('my-slider', 'value'))
def update_output(value):
    date = dfCohFull.dropna()['Reference Date'].unique()[value].replace('-','')
    print('cite:{}_HH.rmli.geo.db'.format(date))
    return 'cite:{}_HH.rmli.geo.db'.format(date)

if __name__ == '__main__': 
    app.run_server(host='0.0.0.0', port=8050, debug=False)