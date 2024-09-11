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
import logging

import dash_bootstrap_components as dbc

from dash import html, Dash
from dotenv import load_dotenv
from routes import add_routes


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
parser.add_argument(
    '--logging-level', type=str,
    help="Level of detail output to logs: \
         DEBUG, INFO, WARNING, ERROR, CRITICAL",
    # use the env variable as default log level (if specified)
    default=str(os.getenv('LOG_LEVEL', 'INFO'))
)
args = parser.parse_args()

logging_level = getattr(logging, args.logging_level.upper(), logging.INFO)

logging.basicConfig(
    level=logging_level,  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filemode='a'  # 'w' to overwrite the log file each time, 'a' to append
)

logger = logging.getLogger(__name__)

app = Dash(__name__,
           prevent_initial_callbacks=True,
           external_stylesheets=[dbc.themes.DARKLY],
           use_pages=True,
           suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
  dash.page_container])

add_routes(server)


if __name__ == '__main__':
    logger.info(
        "Running server at %s:%s",
        args.host,
        args.port)
    # app.run(debug=True, host=args.host, port=args.port)
    app.run(debug=False, host=args.host, port=args.port)
