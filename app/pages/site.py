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
import requests

import dash
import pandas as pd
import logging

from dash import html, callback
from dash.dcc import Graph, Tab, Tabs
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
from dash_leaflet import (
    Map,
    TileLayer,
    CircleMarker,
    Popup
)
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import (
    Output,
    DashProxy,
    Input,
    MultiplexerTransform
)
from pages.components.gc_header import gc_header, gc_line
from global_components import generate_controls
from data_utils import (
    _baseline_csv,
    _coherence_csv,
    _insar_pair_csv,
    _read_baseline,
    _read_coherence,
    _read_insar_pair,
    parse_dates,
    plot_annotation_tab,
    plot_baseline,
    plot_coherence,
    populate_beam_selector,
    config,
    get_latest_quakes_chis_fsdn_site
)
from global_variables import (
    TEMPORAL_HEIGHT
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

curr_info_text = '20220821_HH_20220914_HH.adf.unw.geo.tif'
curr_gc_header_title = 'VRRC InSAR Site Meager 5M3'

# dashboard configuration
TEMPLATE = 'darkly'
TITLE = 'Volcano InSAR Interpretation Workbench'

initial_show_glacier_information = False

# construct dashboard
load_figure_template('darkly')
app = DashProxy(prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()],
                external_stylesheets=[dbc.themes.DARKLY])

tiles_url = "".join((f"/getTileUrl?bucket={TILES_BUCKET}&",
                     f"site={SITE_INI}&",
                     f"beam={BEAM_INI}&",
                     "startdate=20220821&",
                     "enddate=20220914&",
                     "x={x}&y={y}&z={z}"))

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

spatial_view = Map(
    children=[
        TileLayer(),
        generate_controls(overview=False),
        *[
            CircleMarker(
                center=[row['Latitude'], row['Longitude']],
                radius=3*row['Magnitude'],
                fillColor=row['quake_colour'],
                fillOpacity=0.6,
                color='black',
                weight=1,
                children=Popup(
                    html.P([
                        f"""Magnitude: {row['Magnitude']} {row['MagType']}""",
                        html.Br(),
                        f"Date: {row['Time'][0:10]}",
                        html.Br(),
                        f"Depth: {row['Depth/km']} km",
                        html.Br(),
                        f"EventID: {row['#EventID']}",
                        html.Br(),
                    ])
                ),
            )
            for _, row in epicenters_df.sort_values(
                by='#EventID'
                ).iterrows()
        ],
        TileLayer(
            id='tiles',
            url=tiles_url,
            # maxZoom=30,
            # minZoom=1,
            # attribution='&copy; Open Street Map Contributors',
            tms=True,
            # opacity=0.7
        ),
        # generate_legend(overview=False),
    ],
    id='interferogram-bg',
    center=TARGET_CENTRES[INITIAL_TARGET],
    zoom=11,
    # style={'height': '98%', 'width': '98%', 'margin': '0 auto'}
    style={'height': '100%'}
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
# Tabs(id="tabs-example-graph",
#                     value='tab-1-coherence-graph',
#                     children=[Tab(label='Coherence',
#                                   value='tab-1-coherence-graph',
#                                   style=tab_style,
#                                   selected_style=tab_selected_style),
#                               Tab(label='B-Perp',
#                                   value='tab-2-baseline-graph',
#                                   style=tab_style,
#                                   selected_style=tab_selected_style),
#                               Tab(label='Annotations',
#                                   value='tab-3-annotations',
#                                   style=tab_style,
#                                   selected_style=tab_selected_style)
#                               ],
#                     style={'width': '15%',
#                            'height': '25px',
#                            'background-color': 'black'
#                         },
#                     vertical=False)

# LAYOUT
layout = html.Div(
    style={
        'height': '100vh',
        'display': 'flex',
        'flexDirection': 'column',
        'topMargin': 5,
        'bottomMargin': 5,
        # 'background-color': 'white'
    },
    children=[
        # HEADER
        html.Div(id='gc-header-container'),
        html.Div(
            children=gc_line(
                borderWidth=3,
                lineWidth=5,
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
                    children=parse_dates(curr_info_text),
                    style={ 'color': 'black'}
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


"""
Update interferogram display and information text
based on click data and site selection.

Parameters:
- click_data (dict or None): Click data from the 'coherence-matrix' component.
- target_id (str or None): Selected site and beam ID from 'site-dropdown'.

Returns:
- tuple: A tuple containing:
    - str: Updated URL for the 'tiles' component to display the interferogram.
    - dash.html.P: HTML paragraph with information about the interferogram.
"""


@callback(
    Output(component_id='tiles',
           component_property='url',
           allow_duplicate=True),
    Output('curr-info-text', 'children', allow_duplicate=True),
    Input(component_id='coherence-matrix', component_property='clickData'),
    Input('site-dropdown', 'value'),
    Input('tiles', 'zoom'),
    Input('tiles', 'bounds'),
    prevent_initial_call=True
    )
def update_interferogram(click_data, target_id, zoom, bounds):
    """Update interferogram display."""
    if not target_id:
        raise PreventUpdate
    site, beam = target_id.rsplit('_', 1)
    if not click_data:
        url = "".join((f"/getTileUrl?bucket={TILES_BUCKET}&",
                       f"site={SITE_INI}&",
                       f"beam={BEAM_INI}&",
                       "startdate=20220821&",
                       "enddate=20220914&",
                       "x={x}&y={y}&z={z}"))
        return url, ""

    second = pd.to_datetime(click_data['points'][0]['x'])
    delta = pd.Timedelta(click_data['points'][0]['y'], 'days')
    first = second - delta
    first_str = first.strftime('%Y%m%d')
    second_str = second.strftime('%Y%m%d')
    url = "".join((f"/getTileUrl?bucket={TILES_BUCKET}&",
                   f"site={site}&",
                   f"beam={beam}&",
                   f"startdate={first_str}&",
                   f"enddate={second_str}&",
                   "x={x}&y={y}&z={z}"))
    test_url = "".join((f"http://{HOST}:{PORT}",
                        f"/getTileUrl?bucket={TILES_BUCKET}&",
                        f"site={site}&",
                        f"beam={beam}&",
                        f"startdate={first_str}&",
                        f"enddate={second_str}&",
                        "x=0&y=0&z=0"))
    response = requests.get(test_url, timeout=10, verify=False)
    if response.status_code == 200:
        logger.info('Interferogram: %s_HH_%s_HH.adf.wrp.geo.tif',
                    first_str,
                    second_str)
        print(first, second, first_str, second_str)
        return (
            url,
            parse_dates(f'{first_str}_HH_{second_str}_HH.adf.wrp.geo.tif')
        )
    else:
        logger.info('Failed to load: %s_HH_%s_HH.adf.wrp.geo.tif',
                    first_str,
                    second_str)
        raise PreventUpdate


"""
Display a new coherence matrix based on the selected site.

Parameters:
- target_id (str or None): Selected site ID from 'site-dropdown'.

Returns:
- plotly.graph_objs.Figure: Updated coherence matrix plot.
"""


@callback(
    Output(component_id='coherence-matrix',
           component_property='figure',
           allow_duplicate=True),
    Input(component_id='site-dropdown', component_property='value'),
    prevent_initial_call=True
    )
def update_coherence(target_id):
    """Display new coherence matrix."""
    coherence_csv = _coherence_csv(target_id)
    insar_pair_csv = _insar_pair_csv(target_id)
    logger.info('Loading: %s',
                coherence_csv)
    logger.info('Loading: %s',
                insar_pair_csv)
    coherence = _read_coherence(coherence_csv)
    insar_pair = _read_insar_pair(insar_pair_csv)
    return plot_coherence(coherence, insar_pair)


"""
Switch between temporal and spatial baseline plots
based on tab selection and site.

Parameters:
- tab (str): Selected tab ID from 'tabs-example-graph'.
- site (str): Selected site ID from 'site-dropdown'.

Returns:
- plotly.graph_objs.Figure: Updated coherence matrix or baseline plot.
"""


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
    """Switch between temporal and spatial baseline plots"""
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
        return plot_annotation_tab()
    return None


"""
Recenter the map on a new site and update information text.

Parameters:
- target_id (str or None): Selected site ID from 'site-dropdown'.

Returns:
- dict: Updated viewport parameters for the 'interferogram-bg' component.
- dash.html.P: HTML paragraph with information about the new site.
"""


@callback(
    Output(component_id='interferogram-bg',
           component_property='viewport',
           allow_duplicate=True),
    Output('ifg-info', 'children', allow_duplicate=True),
    Input(component_id='site-dropdown', component_property='value'),
    prevent_initial_call=True
    )
def recenter_map(target_id):
    """Center map on new site."""
    coords = TARGET_CENTRES[target_id]
    logger.info('Recentering: %s',
                coords)
    info_text = html.P([''], style={
        'margin': 0,
        'color': 'rgba(255, 255, 255, 0.9)'
        })
    return dict(center=coords,
                zoom=10,
                transition="flyTo"), info_text


"""
Update earthquake markers on the map based on the selected site.

Parameters:
- target_id (str or None): Selected site ID from 'site-dropdown'.

Returns:
- list: Updated layers including earthquake markers for
    the 'interferogram-bg' component.
"""


@callback(
    Output('interferogram-bg', 'children'),
    Input('site-dropdown', 'value'),
    prevent_initial_call=True
)
def update_earthquake_markers(target_id):
    """Update earthquake markers on map."""
    if not target_id:
        raise PreventUpdate
    new_epicenters_df = get_latest_quakes_chis_fsdn_site(
        target_id, TARGET_CENTRES
    )
    if '#EventID' in new_epicenters_df.columns:
        new_markers = [
            CircleMarker(
                center=[row['Latitude'], row['Longitude']],
                radius=3*row['Magnitude'],
                fillColor=row['quake_colour'],
                fillOpacity=0.6,
                color='black',
                weight=1,
                children=Popup(
                    html.P([
                        f"Magnitude: {row['Magnitude']} {row['MagType']}",
                        html.Br(),
                        f"Date: {row['Time'][0:10]}",
                        html.Br(),
                        f"Depth: {row['Depth/km']} km",
                        html.Br(),
                        f"EventID: {row['#EventID']}",
                        html.Br(),
                    ])
                ),
            )
            for index, row in new_epicenters_df.sort_values(
                by='#EventID'
                ).iterrows()
        ]
    else:
        new_markers = []
        logger.info('Note: No earthquakes found')

    base_layers = [
        TileLayer(),
        generate_controls(overview=False),
        TileLayer(
            id='tiles',
            url=(''),
            maxZoom=30,
            minZoom=1,
            attribution='&copy; Open Street Map Contributors',
            tms=True,
            opacity=0.7)
    ]
    all_layers = base_layers + new_markers
    return all_layers


@callback(
    Output(component_id='gc-header-container', component_property='children'),
    Input(component_id='site-dropdown', component_property='value'),
    # prevent_initial_call=True
    )
def update_gc_header_title(target_id):
    """Display new gc header title"""

    site, beam = target_id.rsplit('_', 1)

    return gc_header(f'VRRC InSAR Site {site} {beam}')
