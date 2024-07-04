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

from dash import html, callback
from dash.dcc import Graph, Tab, Tabs
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
from dash_leaflet import (
    Map,
    TileLayer,
)
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import (
    Output,          
    DashProxy,
    Input,
    MultiplexerTransform
)
from global_components import generate_layers_control, generate_legend
from data_utils import (
    _baseline_csv,
    _coherence_csv,
    _read_baseline,
    _read_coherence,
    plot_baseline,
    plot_coherence,
    populate_beam_selector,
    config
)
from global_variables import (
    TEMPORAL_HEIGHT
)

dash.register_page(__name__, path='/site')

# VARIABLES
TILES_BUCKET = config['AWS_TILES_URL']
TARGET_CENTRES_INI = populate_beam_selector(config['API_VRRC_IP'])
TARGET_CENTRES = {i: TARGET_CENTRES_INI[i] for i in sorted(TARGET_CENTRES_INI)}
INITIAL_TARGET = 'Meager_5M3'
SITE_INI, BEAM_INI = INITIAL_TARGET.split('_')

# dashboard configuration
TEMPLATE = 'darkly'
TITLE = 'Volcano InSAR Interpretation Workbench'

initial_show_glacier_information = False

# construct dashboard
load_figure_template('darkly')
app = DashProxy(prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()],
                external_stylesheets=[dbc.themes.DARKLY])

# different components in page layout + styling variables
selector = html.Div(
    title=TITLE,
    children=dbc.InputGroup(
        [
            dbc.InputGroupText('Target_Beam'),
            dbc.Select(
                id='site-dropdown',
                options=list(TARGET_CENTRES.keys()),
                value=INITIAL_TARGET,
            ),
        ]
    ),
)

spatial_view = Map(
    children=[
        TileLayer(),
        generate_layers_control(),
        TileLayer(
            id='tiles',
            url=(
                f'{TILES_BUCKET}/{SITE_INI}/{BEAM_INI}/20220821_20220914/'
                '{z}/{x}/{y}.png'
            ),
            maxZoom=30,
            minZoom=1,
            attribution='&copy; Open Street Map Contributors',
            tms=True,
            opacity=0.7
        ),
        generate_legend(bottom=30),
    ],
    id='interferogram-bg',
    center=TARGET_CENTRES[INITIAL_TARGET],
    zoom=11,
    style={'height': '100%'}
)

temporal_view = Graph(
    id='coherence-matrix',
    figure=plot_coherence(_read_coherence(_coherence_csv(INITIAL_TARGET))),
    style={'height': TEMPORAL_HEIGHT},
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

baseline_tab = Tabs(id="tabs-example-graph",
                    value='tab-1-coherence-graph',
                    children=[Tab(label='Coherence',
                                  value='tab-1-coherence-graph',
                                  style=tab_style,
                                  selected_style=tab_selected_style),
                              Tab(label='B-Perp',
                                  value='tab-2-baseline-graph',
                                  style=tab_style,
                                  selected_style=tab_selected_style),
                              ],
                    style={'width': '10%',
                           'height': '25px'},
                    vertical=False)

# LAYOUT
layout = dbc.Container(
    [
        dbc.Row(dbc.Col(selector, width='auto')),
        dbc.Row(dbc.Col(spatial_view), style={'flexGrow': '1'}),
        dbc.Row(dbc.Col(baseline_tab)),  # add into row below
        dbc.Row(dbc.Col(temporal_view)),
    ],
    fluid=True,
    style={
        'height': '100vh',
        'display': 'flex',
        'flexDirection': 'column',
        'topMargin': 5,
        'bottomMargin': 5,
    }
)


"""
    Callback to Update interferogram display based on 
    click data and selected site.

    Parameters:
    - click_data (dict): Click data from the coherence matrix.
    - target_id (str): Selected site ID from the dropdown.

    Returns:
    - str: URL of the interferogram image to display.

    Raises:
    - PreventUpdate: If no target_id is provided
        or if the requested layer does not exist.
"""


@callback(
    Output(component_id='tiles',
           component_property='url',
           allow_duplicate=True),
    Input(component_id='coherence-matrix', component_property='clickData'),
    Input('site-dropdown', 'value'),
    prevent_initial_call=True)
def update_interferogram(click_data, target_id):
    """Update interferogram display."""
    if not target_id:
        raise PreventUpdate
    SITE, BEAM = target_id.split('_')
    if not click_data:
        return (
            f'{TILES_BUCKET}/{SITE_INI}/{BEAM_INI}/20220821_20220914/'
            '{z}/{x}/{y}.png'
        )

    second = pd.to_datetime(click_data['points'][0]['x'])
    delta = pd.Timedelta(click_data['points'][0]['y'], 'days')
    first = second - delta
    first_str = first.strftime('%Y%m%d')
    second_str = second.strftime('%Y%m%d')
    layer = (
        f'{TILES_BUCKET}/{SITE}/{BEAM}/{first_str}_{second_str}/'
        '{z}/{x}/{y}.png'
    )

    # Checking if the layer exists
    check_url = (layer.replace('{z}', '0')
                 .replace('{x}', '0')
                 .replace('{y}', '0'))
    response = requests.head(check_url)

    if response.status_code == 200:
        print(f'Updating interferogram: {layer}')
        return layer
    # else
    print('Layer does not exist')
    raise PreventUpdate


"""
    Display new coherence matrix for the selected site.

    Parameters:
    - target_id (str): Selected site ID from the dropdown.

    Returns:
    - dict: Plotly figure object of the coherence matrix.
"""


@callback(
    Output(component_id='coherence-matrix',
           component_property='figure',
           allow_duplicate=True),
    Input(component_id='site-dropdown', component_property='value'),
    prevent_initial_call=True)
def update_coherence(target_id):
    """Display new coherence matrix."""
    coherence_csv = _coherence_csv(target_id)
    print(f'Loading: {coherence_csv}')
    coherence = _read_coherence(coherence_csv)

    return plot_coherence(coherence)


"""
    Recenter map view on the coordinates of the selected site.

    Parameters:
    - target_id (str): Selected site ID from the dropdown.

    Returns:
    - dict: New viewport settings for the map.
"""


@callback(
    Output(component_id='interferogram-bg',
           component_property='viewport',
           allow_duplicate=True),
    Input(component_id='site-dropdown', component_property='value'),
    prevent_initial_call=True)
def recenter_map(target_id):
    """Center map on new site."""
    coords = TARGET_CENTRES[target_id]
    print(f'Recentering: {coords}')
    return {"center": coords, "zoom": 10, "transition": 'flyTo'}


"""
    Switch between temporal and spatial baseline plots for the selected site.

    Parameters:
    - tab (str): Tab value indicating the desired plot
        (e.g., 'tab-1-coherence-graph', 'tab-2-baseline-graph').
    - site (str): Selected site ID from the dropdown.

    Returns:
    - dict: Plotly figure object based on the selected tab and site.

    Notes:
    - If 'tab' does not match any recognized value, returns None.
"""


@callback(
    Output(component_id='coherence-matrix',
           component_property='figure',
           allow_duplicate=True),
    [Input(component_id='tabs-example-graph', component_property='value'),
     Input(component_id='site-dropdown', component_property='value')],
    prevent_initial_call=True)
def switch_temporal_viewl(tab, site):
    """Switch between temporal and spatial basleine plots"""
    if tab == 'tab-1-coherence-graph':
        print(f'coherence for {site}')
        return plot_coherence(_read_coherence(_coherence_csv(site)))
    if tab == 'tab-2-baseline-graph':
        print(f'Baseline for {site}')
        return plot_baseline(_read_baseline(_baseline_csv(site)),
                             _read_coherence(_coherence_csv(site)))
    return None
