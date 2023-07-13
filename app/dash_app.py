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
import numpy as np
import pandas as pd

from dash import html, Dash
from dash.dcc import Graph, Tab, Tabs
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
from dash_leaflet import Map, TileLayer, LayersControl, BaseLayer, WMSTileLayer
from dash_extensions.enrich import (Output,
                                    DashProxy,
                                    Input,
                                    MultiplexerTransform)

from plotly.graph_objects import Heatmap
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# app = Dash(__name__, use_pages=True)
app = DashProxy(prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()],
                external_stylesheets=[dbc.themes.DARKLY],
                use_pages=True)

app.layout = html.Div([
	dash.page_container
])

if __name__ == '__main__':
	app.run(debug=True)