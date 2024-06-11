#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
  - Nick Ackerley <nicholas.ackerley@nrcan-rncan.gc.ca>
"""
import argparse

import dash

from dash import html, Dash
import dash_bootstrap_components as dbc
# from dash_extensions.enrich import (DashProxy,
#                                     MultiplexerTransform)

parser = argparse.ArgumentParser(
    description='Serve Volcanic Interpretation Workbench'
)
parser.add_argument(
    '--host', type=str,
    help='Address on which to run the server',
    default='0.0.0.0'
)
parser.add_argument(
    '--port', type=str,
    help="Port on which to run the server",
    default="8050"
)
args = parser.parse_args()

app = Dash(__name__,
           prevent_initial_callbacks=True,
           external_stylesheets=[dbc.themes.DARKLY],
           use_pages=True,)
# app = DashProxy(prevent_initial_callbacks=True,
#                 suppress_callback_exceptions=True,
#                 transforms=[MultiplexerTransform()],
#                 external_stylesheets=[dbc.themes.DARKLY],
#                 use_pages=True)

app.layout = html.Div([
  html.H2(id='test', children='hiii this is testing'),
  dash.page_container
])

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(debug=True, host=args.host, port=args.port)
