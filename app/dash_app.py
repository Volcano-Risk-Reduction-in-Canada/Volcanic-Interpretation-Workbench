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
import os
import dash

from dash import html, Dash
import dash_bootstrap_components as dbc
# from dash_extensions.enrich import (DashProxy,
#                                     MultiplexerTransform)
from dotenv import load_dotenv

# Load environment variables from .env file during development
load_dotenv()

parser = argparse.ArgumentParser(
    description='Serve Volcanic Interpretation Workbench'
)
parser.add_argument(
    '--host', type=str,
    help='Address on which to run the server',
    # use the env variable as default host (if specified)
    default=os.getenv('WORKBENCH_HOST', '0.0.0.0')
)
parser.add_argument(
    '--port', type=str,
    help="Port on which to run the server",
    # use the env variable as default port (if specified)
    default=int(os.getenv('WORKBENCH_PORT', '8050'))
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
  dash.page_container
])

if __name__ == '__main__':
    print(f"Running server at {args.host}:{args.port}")
    app.run(debug=False, host=args.host, port=args.port)
