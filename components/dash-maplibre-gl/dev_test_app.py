#!/usr/bin/python3
"""
Standalone smoke-test harness for the MapLibreMap Dash component.

Mounts MapLibreMap directly with representative props, bypassing the
Volcanic-Interpretation-Workbench app's dependencies on the external VRRC
metadata API and AWS S3 (neither is reachable in this dev/verification
environment). Verifies the component itself: basemap rendering, DEM terrain,
and (using an existing public XYZ tile source's tiling scheme as a stand-in
raster overlay, since the real interferogram tiles require AWS credentials).
"""
import dash
from dash import html
import dash_maplibre_gl as dml

app = dash.Dash(__name__)

BASEMAPS = {
    'topo': {
        'url': (
            'https://server.arcgisonline.com/ArcGIS/rest/services/'
            'World_Topo_Map/MapServer/tile/{z}/{y}/{x}'
        ),
        'attribution': 'Esri',
    },
    'streets': {
        'url': (
            'https://server.arcgisonline.com/ArcGIS/rest/services/'
            'World_Street_Map/MapServer/tile/{z}/{y}/{x}'
        ),
        'attribution': 'Esri',
    },
    'imagery': {
        'url': (
            'https://server.arcgisonline.com/ArcGIS/rest/services/'
            'World_Imagery/MapServer/tile/{z}/{y}/{x}'
        ),
        'attribution': 'Esri',
    },
}

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
            'geometry': {'type': 'Point', 'coordinates': [-123.62, 50.61]},
            'properties': {
                'magnitude': 1.8, 'magType': 'ML', 'time': '2023-06-01T00:00:00',
                'depthKm': 2.3, 'eventId': 'TEST2', 'quakeColour': 'yellow',
            },
        },
    ],
}

app.layout = html.Div(
    style={'height': '100vh', 'width': '100vw'},
    children=[
        dml.MapLibreMap(
            id='test-map',
            initialViewState=MEAGER,
            basemaps=BASEMAPS,
            activeBasemap='topo',
            demTiles='https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png',
            demEncoding='terrarium',
            terrainExaggeration=1.5,
            earthquakeData=EARTHQUAKES,
            style={'height': '100%', 'width': '100%'},
        ),
    ],
)

if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port=8060, debug=False)
