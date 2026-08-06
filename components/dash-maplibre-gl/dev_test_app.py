#!/usr/bin/python3
"""
Standalone smoke-test harness for the MapLibreMap Dash component.

Mounts MapLibreMap with the same Darkly Bootstrap theme, basemap switcher,
and earthquake popup wiring as the real site page, bypassing only the
Volcanic-Interpretation-Workbench app's dependencies on the external VRRC
metadata API and AWS S3 (neither is reachable in this dev/verification
environment). Useful for reproducing page-theme-related rendering bugs
(e.g. Darkly CSS bleeding into MapLibre's native controls/popups) without
needing the live backend.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from flask import Response, request  # noqa: E402
import requests  # noqa: E402
import dash  # noqa: E402
from dash import html  # noqa: E402
import dash_bootstrap_components as dbc  # noqa: E402
import dash_maplibre_gl as dml  # noqa: E402
from global_components import generate_basemap_switcher  # noqa: E402
from global_variables import (  # noqa: E402
    MAPLIBRE_BASEMAPS,
    MAPLIBRE_DEFAULT_BASEMAP,
    DEM_ENCODING,
    DEM_TERRAIN_EXAGGERATION,
)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])


@app.server.route('/getDemTileUrl')
def get_dem_tile_url():
    """Same-origin DEM proxy, mirroring app/routes.py's real route --
    see the CORS note there for why this can't just point at S3 directly."""
    x = int(request.args.get('x'))
    y = int(request.args.get('y'))
    z = int(request.args.get('z'))
    upstream_url = (
        f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
    )
    response = requests.get(upstream_url, timeout=10)
    return Response(response.content, mimetype='image/png')


# Meager Creek volcanic complex, BC -- steep terrain, good for verifying
# DEM relief.
MEAGER = {'longitude': -123.60, 'latitude': 50.64, 'zoom': 11, 'pitch': 60, 'bearing': -30}

EARTHQUAKES = {
    'type': 'FeatureCollection',
    'features': [
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-123.55, 50.68]},
            'properties': {
                'magnitude': 3.2, 'magType': 'ML', 'time': '2024-01-01T00:00:00',
                'depthKm': 5.1, 'eventId': 'TEST1', 'quakeColour': 'red',
            },
        },
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-123.60, 50.64]},
            'properties': {
                'magnitude': 4.5, 'magType': 'ML', 'time': '2023-06-01T00:00:00',
                'depthKm': 2.3, 'eventId': 'TEST2', 'quakeColour': 'yellow',
            },
        },
    ],
}

app.layout = html.Div(
    style={'height': '100vh', 'width': '100vw', 'position': 'relative'},
    children=[
        dml.MapLibreMap(
            id='test-map',
            initialViewState=MEAGER,
            basemaps=MAPLIBRE_BASEMAPS,
            activeBasemap=MAPLIBRE_DEFAULT_BASEMAP,
            demTiles='/getDemTileUrl?z={z}&x={x}&y={y}',
            demEncoding=DEM_ENCODING,
            terrainExaggeration=DEM_TERRAIN_EXAGGERATION,
            earthquakeData=EARTHQUAKES,
            style={'height': '100%', 'width': '100%'},
        ),
        generate_basemap_switcher(active=MAPLIBRE_DEFAULT_BASEMAP),
    ],
)

if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port=8060, debug=False)
