#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2026 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>

Local dev page for the site page's Timeseries tab, needing neither the VRRC
API nor S3. It mounts the site page's map (basemaps, DEM terrain/hillshade;
no interferogram or earthquakes) and bottom-pane tabs, wired to the real
Timeseries code: pages/components/timeseries_components.py (tab layout and
callbacks) and routes.py (/getPointTile, /getDemTileUrl). Site/beam options
are whichever have point data under app/Data (see
scripts/build_point_tiles.py). Basemap and DEM tiles still come from the
internet.

Run from the repo root:
    venv/bin/python app/dev_timeseries_app.py [--port 8051]
"""
import argparse
import glob
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)
# Data paths (app/Data/...) are relative to the repo root.
os.chdir(os.path.dirname(APP_DIR))

import dash  # noqa: E402
from dash import html, callback, Input, Output  # noqa: E402
from dash.dcc import Store, Tab, Tabs  # noqa: E402
from dash.exceptions import PreventUpdate  # noqa: E402
from dash_bootstrap_templates import load_figure_template  # noqa: E402
import dash_bootstrap_components as dbc  # noqa: E402
import dash_maplibre_gl as dml  # noqa: E402

from data_utils import has_point_timeseries, read_point_stats  # noqa: E402
from global_components import (  # noqa: E402
    generate_basemap_monochrome_control,
    generate_basemap_switcher,
)
from global_variables import (  # noqa: E402
    DEM_ENCODING,
    DEM_TERRAIN_EXAGGERATION,
    DEM_TILE_URL,
    MAPLIBRE_BASEMAPS,
    MAPLIBRE_DEFAULT_BASEMAP,
    TEMPORAL_HEIGHT,
    TIMESERIES_BASEMAP,
)
# Also registers the Timeseries tab's callbacks.
from pages.components.timeseries_components import (  # noqa: E402
    TIMESERIES_TAB,
    point_source,
    timeseries_tab_layout,
)
from routes import add_routes  # noqa: E402

OTHER_TAB = 'tab-1-coherence-graph'
TAB_STYLE = {'color': 'black', 'padding': '6px', 'fontWeight': 'bold',
             'font-size': '11px'}
TAB_SELECTED_STYLE = {**TAB_STYLE, 'backgroundColor': '#119DFF'}


def local_targets():
    """Site/beam ids ('Meager_5M10') with point data under app/Data."""
    targets = []
    for mbtiles in glob.glob('app/Data/*/*/*_points.mbtiles'):
        target_id = os.path.basename(mbtiles)[:-len('_points.mbtiles')]
        if has_point_timeseries(target_id):
            targets.append(target_id)
    return sorted(targets)


def bounds_centre(target_id):
    west, south, east, north = read_point_stats(target_id)['bounds']
    return (west + east) / 2, (south + north) / 2


TARGETS = local_targets()
if not TARGETS:
    sys.exit('No point data found: build it with scripts/build_point_tiles.py')
INITIAL_TARGET = TARGETS[0]
INITIAL_LON, INITIAL_LAT = bounds_centre(INITIAL_TARGET)

load_figure_template('darkly')
app = dash.Dash(
    __name__,
    title='Timeseries dev page',
    external_stylesheets=[dbc.themes.DARKLY],
    # Same as the real app (dash_app.py), so callbacks behave the same.
    prevent_initial_callbacks=True,
    suppress_callback_exceptions=True,
)
add_routes(app.server)

# Starts already in Timeseries mode (what toggle_timeseries_mode sets on
# entering the tab); the other tab exercises leaving/re-entering it.
app.layout = html.Div(
    style={'height': '100vh', 'display': 'flex', 'flexDirection': 'column',
           'background-color': 'white'},
    children=[
        Store(id='ts-restore', data={'basemap': MAPLIBRE_DEFAULT_BASEMAP}),
        html.Div(
            [
                html.H6('Timeseries dev page (local data only)',
                        style={'color': 'black', 'margin': 0}),
                dbc.InputGroup(
                    [
                        dbc.InputGroupText('Target Beam'),
                        dbc.Select(id='site-dropdown', options=TARGETS,
                                   value=INITIAL_TARGET),
                    ],
                    size='sm', style={'width': 'auto'},
                ),
            ],
            style={'display': 'flex', 'justify-content': 'space-between',
                   'align-items': 'center', 'padding': '6px 20px'},
        ),
        html.Div(
            style={'position': 'relative', 'flexGrow': 1},
            children=[
                dml.MapLibreMap(
                    id='interferogram-bg',
                    initialViewState={
                        'longitude': INITIAL_LON, 'latitude': INITIAL_LAT,
                        'zoom': 11, 'pitch': 0, 'bearing': 0,
                    },
                    basemaps=MAPLIBRE_BASEMAPS,
                    activeBasemap=TIMESERIES_BASEMAP,
                    demTiles=DEM_TILE_URL,
                    demEncoding=DEM_ENCODING,
                    terrainExaggeration=DEM_TERRAIN_EXAGGERATION,
                    interferogramVisible=False,
                    pointSource=point_source(INITIAL_TARGET),
                    style={'height': '100%'},
                ),
                generate_basemap_switcher(active=TIMESERIES_BASEMAP),
                generate_basemap_monochrome_control(),
            ],
        ),
        Tabs(
            id='tabs-example-graph',
            value=TIMESERIES_TAB,
            children=[
                Tab(label='Other tab', value=OTHER_TAB, style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE),
                Tab(label='Timeseries', value=TIMESERIES_TAB,
                    style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
            ],
            style={'width': '15%', 'height': '25px'},
        ),
        html.Div(id='temporal_view',
                 children=timeseries_tab_layout(INITIAL_TARGET)),
    ],
)


@callback(
    Output('temporal_view', 'children'),
    Input('tabs-example-graph', 'value'),
    Input('site-dropdown', 'value'),
)
def switch_temporal_view(tab, target_id):
    """Dev stand-in for site.py's switch_temporal_view."""
    if tab == TIMESERIES_TAB:
        return timeseries_tab_layout(target_id)
    return html.Div(
        'Coherence / B-Perp / Annotations need the VRRC API and S3, so '
        'they are not on this dev page. Switching here takes the map out '
        'of Timeseries mode.',
        style={'color': 'black', 'padding': '20px', 'height': TEMPORAL_HEIGHT}
    )


@callback(
    Output('interferogram-bg', 'activeBasemap'),
    Input('basemap-switcher', 'value'),
)
def update_basemap(active_basemap):
    """Same as site.py's update_basemap."""
    if not active_basemap:
        raise PreventUpdate
    return active_basemap


@callback(
    Output('interferogram-bg', 'basemapMonochrome'),
    Input('basemap-monochrome-toggle', 'value'),
)
def update_basemap_monochrome(monochrome):
    """Same as site.py's update_basemap_monochrome."""
    return bool(monochrome)


@callback(
    Output('interferogram-bg', 'flyTo'),
    Input('site-dropdown', 'value'),
)
def recenter_map(target_id):
    """Fly to the selected site/beam's point data."""
    longitude, latitude = bounds_centre(target_id)
    return {'longitude': longitude, 'latitude': latitude, 'zoom': 11,
            'duration': 2000}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Local dev page for the site page Timeseries tab')
    parser.add_argument('--port', type=int, default=8051)
    args = parser.parse_args()
    app.run(debug=True, host='localhost', port=args.port, threaded=True)
