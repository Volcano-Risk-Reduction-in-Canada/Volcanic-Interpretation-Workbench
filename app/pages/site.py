#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2024 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
  - Nick Ackerley <nicholas.ackerley@nrcan-rncan.gc.ca>
  - Mandip Singh Sond <mandip.sond@nrcan-rncan.gc.ca>
"""
import logging
import requests
import dash
import pandas as pd

from dash import html, callback
from dash.dcc import Graph, Tab, Tabs
from dash.exceptions import PreventUpdate
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
import dash_maplibre_gl as dml
from dash_extensions.enrich import (
    Output,
    DashProxy,
    Input,
    State,
    MultiplexerTransform
)
from pages.components.gc_header import gc_header, gc_line
from global_components import (
    generate_basemap_monochrome_control,
    generate_basemap_switcher,
    generate_interferogram_opacity_control,
    generate_legend_visibility_control,
    get_glacier_wms_overlay,
)
from data_utils import (
    _baseline_csv,
    _coherence_csv,
    _insar_pair_csv,
    _read_baseline,
    _read_coherence,
    _read_insar_pair,
    epicenters_df_to_geojson,
    parse_dates,
    plot_annotation_tab,
    plot_baseline,
    plot_coherence,
    populate_beam_selector,
    config,
    get_latest_quakes_chis_fsdn_site
)
from global_variables import (
    TEMPORAL_HEIGHT,
    MAPLIBRE_BASEMAPS,
    MAPLIBRE_DEFAULT_BASEMAP,
    DEM_TILE_URL,
    DEM_ENCODING,
    DEM_TERRAIN_EXAGGERATION,
)

logger = logging.getLogger(__name__)

dash.register_page(__name__, path='/site')

# VARIABLES
TILES_BUCKET = config['AWS_TILES_URL']
HOST = config['WORKBENCH_HOST']
PORT = config['WORKBENCH_PORT']
TARGET_CENTRES_INI = populate_beam_selector(config['API_VRRC_IP'])
TARGET_CENTRES = {i: TARGET_CENTRES_INI[i] for i in sorted(TARGET_CENTRES_INI)}
INITIAL_TARGET = 'Meager_5M3'
SITE_INI, BEAM_INI = INITIAL_TARGET.rsplit('_', 1)

epicenters_df = get_latest_quakes_chis_fsdn_site(
    INITIAL_TARGET, TARGET_CENTRES
)

# init_info_text = '20220821_HH_20220914_HH.adf.unw.geo.tif'

# dashboard configuration
TEMPLATE = 'darkly'
TITLE = 'Volcano InSAR Interpretation Workbench'

# construct dashboard
load_figure_template('darkly')
app = DashProxy(prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()],
                external_stylesheets=[dbc.themes.DARKLY])


def _interferogram_tile_url(site, beam, startdate, enddate):
    """Build the /getTileUrl XYZ template for a given site/beam/date pair."""
    return "".join((
        f"/getTileUrl?bucket={TILES_BUCKET}&",
        f"site={site}&",
        f"beam={beam}&",
        f"startdate={startdate}&",
        f"enddate={enddate}&",
        "x={x}&y={y}&z={z}"
    ))


# different components in page layout + styling variables
selector = html.Div(
    title=TITLE,
    children=dbc.InputGroup(
        [
            dbc.InputGroupText(
                'Target Beam',
                style={'height': '30px'}
            ),
            dbc.Select(
                id='site-dropdown',
                options=list(TARGET_CENTRES.keys()),
                value=INITIAL_TARGET,
                size='sm',
                style={'height': '30px'}
            ),
        ],
        style={
            'height': '30px',
            'bottom': '10px'
        }
    ),
)

spatial_view = html.Div(
    id='spatial_view_container',
    style={'position': 'relative', 'height': '100%', 'flexGrow': '1'},
    children=[
        dml.MapLibreMap(
            id='interferogram-bg',
            initialViewState={
                'longitude': TARGET_CENTRES[INITIAL_TARGET][1],
                'latitude': TARGET_CENTRES[INITIAL_TARGET][0],
                'zoom': 11,
                'pitch': 0,
                'bearing': 0,
            },
            basemaps=MAPLIBRE_BASEMAPS,
            activeBasemap=MAPLIBRE_DEFAULT_BASEMAP,
            interferogramTileUrl=_interferogram_tile_url(
                SITE_INI, BEAM_INI, '20220821', '20220914'
            ),
            demTiles=DEM_TILE_URL,
            demEncoding=DEM_ENCODING,
            terrainExaggeration=DEM_TERRAIN_EXAGGERATION,
            earthquakeData=epicenters_df_to_geojson(epicenters_df),
            # TEMPORARY: disabled to isolate whether the glacier WMS
            # overlay (an external, third-party service) is what's
            # preventing DEM terrain tiles from loading. Revert once
            # confirmed either way.
            # wmsOverlay=get_glacier_wms_overlay(),
            style={'height': '100%'},
        ),
        generate_basemap_switcher(active=MAPLIBRE_DEFAULT_BASEMAP),
        generate_interferogram_opacity_control(),
        generate_basemap_monochrome_control(),
        generate_legend_visibility_control(overview=False),
    ]
)

temporal_view = html.Div(
    id='temporal_view',
    children=[
        Graph(
            id='coherence-matrix',
            figure=plot_coherence(
                _read_coherence(_coherence_csv(INITIAL_TARGET)),
                _read_insar_pair(_insar_pair_csv(INITIAL_TARGET))
            ),
            style={'height': TEMPORAL_HEIGHT},
        )
    ]
)

tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'color': 'black',
    'padding': '6px',
    'fontWeight': 'bold',
    'font-size': '11px',
}

tab_selected_style = {
    'align-items': 'top',
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'black',
    'font-size': '11px',
    'padding': '6px'
}

baseline_tab = html.Div(
    children=[
        Tabs(
            id="tabs-example-graph",
            value='tab-1-coherence-graph',
            children=[
                Tab(
                    label='Coherence',
                    value='tab-1-coherence-graph',
                    style=tab_style,
                    selected_style=tab_selected_style
                ),
                Tab(
                    label='B-Perp',
                    value='tab-2-baseline-graph',
                    style=tab_style,
                    selected_style=tab_selected_style
                ),
                Tab(
                    label='Annotations',
                    value='tab-3-annotations',
                    style=tab_style,
                    selected_style=tab_selected_style
                )
            ],
            style={
                'width': '15%',
                'height': '25px',
                'background-color': 'black'
            },
            vertical=False
        )
    ],
    style={
        'width': '100%',
        'background-color': 'black'
    }
)

# LAYOUT
layout = html.Div(
    style={
        'height': '100vh',
        'display': 'flex',
        'flexDirection': 'column',
        'topMargin': 5,
        'bottomMargin': 5,
    },
    children=[
        # HEADER
        html.Div(id='gc-header-container'),
        html.Div(
            children=gc_line(
                border_width=3,
                line_width=5,
                color='red',
                margin='0 0 10px 20px'
            ),
            style={
                'background-color': 'white',
                'justify-content': 'flex-start'
            }
        ),
        html.Div(
            children=[
                html.H6(
                    id="curr-info-text",
                    children='',
                    style={'color': 'black'}
                ),
                # selector
                dbc.Row(dbc.Col(
                    selector,
                    width='auto',
                    style={'height': '20px'}
                ))
            ],
            style={
                'display': 'flex',
                'flex-direction': 'row',
                'justify-content': 'space-between',
                'background-color': 'white',
                'padding': '0 20px 10px'
            }
        ),
        # Main layout container
        dbc.Container(
            [
                # MAP
                dbc.Row(
                    dbc.Col(spatial_view),
                    style={'flexGrow': '1', "background-color": 'white'}
                ),
                # TABS Selector
                dbc.Row(
                    dbc.Col(baseline_tab),
                    style={"background-color": 'white'}
                ),
                # TABS Information
                html.Div(
                    children=dbc.Row(
                        dbc.Col(temporal_view),
                        style={"background-color": 'white'}
                    ),
                    id='temporal_view'
                )
            ],
            fluid=True,
            style={
                'height': '98vh',
                'display': 'flex',
                'flexDirection': 'column',
                'topMargin': 5,
                'bottomMargin': 5,
            },
        )
    ]
)


@callback(
    Output(component_id='interferogram-bg',
           component_property='interferogramTileUrl',
           allow_duplicate=True),
    Output('curr-info-text', 'children', allow_duplicate=True),
    Input(component_id='coherence-matrix', component_property='clickData'),
    Input('site-dropdown', 'value'),
    prevent_initial_call=True
)
def update_interferogram(click_data, target_id):
    """
    Update interferogram display and information text
    based on click data and site selection.

    Parameters:
    - click_data (dict or None): Click data from the
        'coherence-matrix' component.
    - target_id (str or None): Selected site and beam ID from 'site-dropdown'.

    Returns:
    - tuple: A tuple containing:
        - str: Updated tile URL template for the 'interferogram-bg'
            MapLibreMap component.
        - dash.html.P: HTML paragraph with information about the interferogram.
    """
    if not target_id:
        raise PreventUpdate
    site, beam = target_id.rsplit('_', 1)
    if not click_data:
        return _interferogram_tile_url(
            SITE_INI, BEAM_INI, '20220821', '20220914'
        ), ""

    second = pd.to_datetime(click_data['points'][0]['x'])
    delta = pd.Timedelta(click_data['points'][0]['y'], 'days')
    first = second - delta
    first_str = first.strftime('%Y%m%d')
    second_str = second.strftime('%Y%m%d')
    url = _interferogram_tile_url(site, beam, first_str, second_str)
    test_url = "".join((f"http://{HOST}:{PORT}",
                        f"/getTileUrl?bucket={TILES_BUCKET}&",
                        f"site={site}&",
                        f"beam={beam}&",
                        f"startdate={first_str}&",
                        f"enddate={second_str}&",
                        "x=0&y=0&z=0"))
    response = requests.get(test_url, timeout=10)
    if response.status_code == 200:
        logger.info('Interferogram: %s_HH_%s_HH.adf.wrp.geo.tif',
                    first_str,
                    second_str)
        print('SUCCESS UPDATE INTERFEROGRAM')
        return (
            url,
            parse_dates(f'{first_str}_HH_{second_str}_HH.adf.wrp.geo.tif')
        )
    # else:
    logger.info('Failed to load: %s_HH_%s_HH.adf.wrp.geo.tif',
                first_str,
                second_str)
    raise PreventUpdate


@callback(
    Output(component_id='coherence-matrix',
           component_property='figure',
           allow_duplicate=True),
    Input(component_id='site-dropdown', component_property='value'),
    prevent_initial_call=True
)
def update_coherence(target_id):
    """
    Display a new coherence matrix based on the selected site.

    Parameters:
    - target_id (str or None): Selected site ID from 'site-dropdown'.

    Returns:
    - plotly.graph_objs.Figure: Updated coherence matrix plot.
    """
    print('IM HERE!!!')
    coherence_csv = _coherence_csv(target_id)
    insar_pair_csv = _insar_pair_csv(target_id)
    logger.info('Loading: %s',
                coherence_csv)
    logger.info('Loading: %s',
                insar_pair_csv)
    coherence = _read_coherence(coherence_csv)
    insar_pair = _read_insar_pair(insar_pair_csv)
    print(coherence, insar_pair)
    return plot_coherence(coherence, insar_pair)


def _relayout_range(relayout_data, axis):
    """
    Pull an (min, max) range for the given axis ('xaxis'/'yaxis') out of a
    Plotly relayoutData payload, if the user's interaction changed it.

    Returns None if relayout_data doesn't carry an explicit range for this
    axis (e.g. it was some other relayout event, like an autoscale/reset or
    a dragmode change).
    """
    if relayout_data is None:
        return None
    lo_key, hi_key = f'{axis}.range[0]', f'{axis}.range[1]'
    if lo_key in relayout_data and hi_key in relayout_data:
        return (relayout_data[lo_key], relayout_data[hi_key])
    if f'{axis}.range' in relayout_data:
        return tuple(relayout_data[f'{axis}.range'])
    return None


@callback(
    Output(component_id='coherence-matrix',
           component_property='figure',
           allow_duplicate=True),
    Input(component_id='coherence-matrix', component_property='relayoutData'),
    State(component_id='site-dropdown', component_property='value'),
    State(component_id='tabs-example-graph', component_property='value'),
    prevent_initial_call=True
)
def update_coherence_view(relayout_data, target_id, tab):
    """
    Re-trim and re-render the coherence matrix to whatever window the user
    just panned or zoomed to, instead of loading/plotting the full history.

    Parameters:
    - relayout_data (dict or None): Plotly relayout event data from the
        'coherence-matrix' component (fired on pan/zoom/autoscale).
    - target_id (str or None): Currently selected site from 'site-dropdown'.
    - tab (str): Currently selected tab from 'tabs-example-graph'. The
        B-Perp/Annotations tabs reuse the same 'coherence-matrix' id for a
        different plot, so this callback must stay out of their way.

    Returns:
    - plotly.graph_objs.Figure: Coherence matrix re-plotted for the visible
        window, or dash.exceptions.PreventUpdate if the event carried no
        usable range (e.g. an autoscale/reset or an unrelated relayout), or
        the coherence tab isn't the one currently showing.
    """
    if not target_id or tab != 'tab-1-coherence-graph':
        raise PreventUpdate
    x_range = _relayout_range(relayout_data, 'xaxis')
    y_range = _relayout_range(relayout_data, 'yaxis')
    if x_range is None and y_range is None:
        raise PreventUpdate

    coherence_csv = _coherence_csv(target_id)
    insar_pair_csv = _insar_pair_csv(target_id)
    coherence = _read_coherence(coherence_csv)
    insar_pair = _read_insar_pair(insar_pair_csv)
    return plot_coherence(
        coherence, insar_pair, x_range=x_range, y_range=y_range
    )


@callback(
    Output(
        component_id='temporal_view',
        component_property='children',
        allow_duplicate=True
    ),
    [Input(component_id='tabs-example-graph', component_property='value'),
     Input(component_id='site-dropdown', component_property='value')],
    prevent_initial_call=True
)
def switch_temporal_view(tab, site):
    """
    Switch between temporal and spatial baseline plots
    based on tab selection and site.

    Parameters:
    - tab (str): Selected tab ID from 'tabs-example-graph'.
    - site (str): Selected site ID from 'site-dropdown'.

    Returns:
    - plotly.graph_objs.Figure: Updated coherence matrix or baseline plot.
    """
    if tab == 'tab-1-coherence-graph':
        logger.info('coherence for %s',
                    site)
        return Graph(
            id='coherence-matrix',
            figure=plot_coherence(
                _read_coherence(_coherence_csv(site)),
                _read_insar_pair(_insar_pair_csv(site))
            ),
            style={'height': TEMPORAL_HEIGHT},
        )
    if tab == 'tab-2-baseline-graph':
        logger.info('Baseline for %s',
                    site)
        return Graph(
            id='coherence-matrix',
            figure=plot_baseline(
                _read_baseline(_baseline_csv(site)),
                _read_coherence(_coherence_csv(site))
            ),
            style={'height': TEMPORAL_HEIGHT},
        )
    if tab == 'tab-3-annotations':
        logger.info('annotations for %s', site)
        return plot_annotation_tab(site)
    return None


@callback(
    Output(
        component_id='interferogram-bg',
        component_property='flyTo',
    ),
    Input(component_id='site-dropdown', component_property='value'),
)
def recenter_map(target_id):
    """
    Fly the map to the newly selected site's centre.

    Parameters:
    - target_id (str or None): Selected site ID from 'site-dropdown'.

    Returns:
    - dict: {longitude, latitude, zoom, duration} for the 'interferogram-bg'
        MapLibreMap component's flyTo trigger.
    """
    coords = TARGET_CENTRES[target_id]
    logger.info('Recentering: %s',
                coords)
    # TARGET_CENTRES stores [latitude, longitude]; MapLibre wants
    # {longitude, latitude} -- swap explicitly or the map flies to the
    # wrong hemisphere.
    return {
        'longitude': coords[1],
        'latitude': coords[0],
        'zoom': 10,
        'duration': 2000,
    }


@callback(
    Output('interferogram-bg', 'earthquakeData'),
    Input('site-dropdown', 'value'),
    prevent_initial_call=True
)
def update_earthquake_markers(target_id):
    """
    Update earthquake markers on the map based on the selected site.

    Parameters:
    - target_id (str or None): Selected site ID from 'site-dropdown'.

    Returns:
    - dict: GeoJSON FeatureCollection of earthquake epicenters for the
        'interferogram-bg' MapLibreMap component's earthquakeData prop.
    """
    if not target_id:
        raise PreventUpdate
    new_epicenters_df = get_latest_quakes_chis_fsdn_site(
        target_id, TARGET_CENTRES
    )
    return epicenters_df_to_geojson(new_epicenters_df)


@callback(
    Output('interferogram-bg', 'activeBasemap'),
    Input('basemap-switcher', 'value'),
    prevent_initial_call=True
)
def update_basemap(active_basemap):
    """
    Switch the MapLibre map's visible basemap layer.

    Parameters:
    - active_basemap (str or None): Selected basemap key from
        'basemap-switcher'.

    Returns:
    - str: The basemap key to pass through to the 'interferogram-bg'
        MapLibreMap component's activeBasemap prop.
    """
    if not active_basemap:
        raise PreventUpdate
    return active_basemap


@callback(
    Output('interferogram-bg', 'interferogramOpacity'),
    Input('interferogram-opacity-slider', 'value'),
    prevent_initial_call=True
)
def update_interferogram_opacity(opacity):
    """
    Adjust the MapLibre map's interferogram raster layer opacity.

    Parameters:
    - opacity (float or None): Selected value from
        'interferogram-opacity-slider'.

    Returns:
    - float: The opacity to pass through to the 'interferogram-bg'
        MapLibreMap component's interferogramOpacity prop.
    """
    if opacity is None:
        raise PreventUpdate
    return opacity


@callback(
    Output('interferogram-bg', 'basemapMonochrome'),
    Input('basemap-monochrome-toggle', 'value'),
    prevent_initial_call=True
)
def update_basemap_monochrome(monochrome):
    """
    Toggle the MapLibre map's active basemap between full color and
    monochrome.

    Parameters:
    - monochrome (bool): Checked state of 'basemap-monochrome-toggle'.

    Returns:
    - bool: The value to pass through to the 'interferogram-bg'
        MapLibreMap component's basemapMonochrome prop.
    """
    return bool(monochrome)


@callback(
    Output(component_id='gc-header-container', component_property='children'),
    Input(component_id='site-dropdown', component_property='value'),
    # prevent_initial_call=True
)
def update_gc_header_title(target_id):
    """Display new gc header title"""

    site, beam = target_id.rsplit('_', 1)

    return gc_header(f'VRRC InSAR Site {site} {beam}')
