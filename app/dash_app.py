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

#Dummy Coherence Pair Data
dfCohFull = pd.read_csv('app/Data/coherenceMatrixMeagerCompleteNan.csv')
fig2 = px.imshow(np.rot90(np.fliplr(dfCohFull['Coherence'].to_numpy().reshape(70,70))),
                 x=dfCohFull['Reference Date'].unique(),
                 y=dfCohFull['Pair Date'].unique(),
                 color_continuous_scale='RdBu_r'
                )
fig2.update_yaxes(autorange=True) 


app.layout = html.Div(id = 'parent', children = [
    html.H1(id='H1', children='Volcano InSAR Interpretation Workbench', style = {'textAlign':'center',\
                                            'marginTop':40,'marginBottom':40}),
    html.Div(style={'width': '5%','display': 'inline-block'}),
    html.Div(
        dcc.Graph(id='graph', figure=fig2), #style={'width': '500px', 'height': '500px'}),
        style={'width': '35%', 'display': 'inline-block', 'height': '450px'}),

    html.Div(style={'width': '5%','display': 'inline-block'}),

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
                dl.WMSTileLayer(url="http://localhost:8080/geoserver/Meager_5M3A/wms?",
                                layers="cite:meager_bedem_subset_10N_hs",
                                format="image/png",
                                transparent=True,
                                opacity=1.0),
                dl.WMSTileLayer(id='map',
                                url="http://localhost:8080/geoserver/Meager_5M3A/wms?",
                                layers="cite:20210717_HH_20210903_HH.adf.wrp.geo.crop",
                                format="image/png",
                                transparent=True,
                                opacity=0.6),
                    ],
                center=[50.64, -123.6],
                zoom=12,
                # style={'width': '45%','display': 'inline-block', 'height': '450px'}
                ),
        style={'width': '50%','display': 'inline-block', 'height': '450px'}
        ),
    ])


@app.callback(
    # Output(component_id="output", component_property="children"),
    Output(component_id="map", component_property="layers"),
    Input(component_id="graph", component_property="clickData"))
def update_datepair(clickData):
    if not clickData:
        return 'cite:20210717_HH_20210903_HH.adf.wrp.geo.crop'
    dates='{}_HH_{}_HH'.format(json.dumps(clickData['points'][0]['x'], indent=2),
                               json.dumps(clickData['points'][0]['y'], indent=2))
    dates = dates.replace('-','').replace('"','')
    return'cite:{}.adf.wrp.geo.crop'.format(dates)


if __name__ == '__main__': 
    app.run_server(host='0.0.0.0', port=8051, debug=True)