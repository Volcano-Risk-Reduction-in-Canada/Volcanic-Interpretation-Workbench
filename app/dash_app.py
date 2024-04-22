#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
  - Nick Ackerley <nicholas.ackerley@nrcan-rncan.gc.ca>
"""

import dash

from dash import html, Dash
import dash_bootstrap_components as dbc
# from dash_extensions.enrich import (DashProxy,
#                                     MultiplexerTransform)

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
    app.run(debug=True)
