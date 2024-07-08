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
from global_components import generate_controls, generate_layers_control
from data_utils import (
    _baseline_csv,
    _coherence_csv,
    _read_baseline,
    _read_coherence,
    plot_baseline,
    plot_coherence,
    populate_beam_selector,
    config,
    get_latest_quakes_chis_fsdn_site
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
SITE_INI, BEAM_INI = INITIAL_TARGET.rsplit('_', 1)

epicenters_df = get_latest_quakes_chis_fsdn_site(
    INITIAL_TARGET, TARGET_CENTRES
)

# dashboard configuration
TEMPLATE = 'darkly'
TITLE = 'Volcano InSAR Interpretation Workbench'

initial_show_glacier_information = False

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
        # generate_legend(overview=False),
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

ini_info_text = html.P([
    '20220821_HH_20220914_HH.adf.unw.geo.tif'
], style={
    'margin': 0,
    'color': 'rgba(255, 255, 255, 0.9)',
})

ifg_info = html.Div(
    ini_info_text,
    id='ifg-info',
    style={
        'position': 'absolute',
        'top': '1.5px',
        'right': '11px',
        'width': '340px',
        'height': '35px',
        'backgroundColor': 'rgba(255, 255, 255, 0.1)',
        'padding': '10px',
        'borderRadius': '5px',
        'boxShadow': '0px 0px 10px rgba(0, 0, 0, 0.1)',
        'zIndex': '1000',
        'display': 'flex',
        'alignItems': 'center',
    }
)

# LAYOUT
layout = dbc.Container(
    [
        dbc.Row(dbc.Col(selector, width='auto')),
        dbc.Row(dbc.Col(spatial_view), style={'flexGrow': '1'}),
        dbc.Row(dbc.Col(baseline_tab)),  # add into row below
        dbc.Row(dbc.Col(temporal_view)),
        dbc.Row(dbc.Col(ifg_info)),
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


@callback(
    Output(component_id='tiles',
           component_property='url',
           allow_duplicate=True),
    Output('ifg-info', 'children', allow_duplicate=True),
    Input(component_id='coherence-matrix', component_property='clickData'),
    Input('site-dropdown', 'value'),
    prevent_initial_call=True
    )
def update_interferogram(click_data, target_id):
    """Update interferogram display."""
    if not target_id:
        raise PreventUpdate
    site, beam = target_id.rsplit('_', 1)
    if not click_data:
        return (
            f'{TILES_BUCKET}/{SITE_INI}/{BEAM_INI}/20220821_20220914/'
            '{z}/{x}/{y}.png',
            ""
        )
    second = pd.to_datetime(click_data['points'][0]['x'])
    delta = pd.Timedelta(click_data['points'][0]['y'], 'days')
    first = second - delta
    first_str = first.strftime('%Y%m%d')
    second_str = second.strftime('%Y%m%d')
    layer = (
        f'{TILES_BUCKET}/{site}/{beam}/{first_str}_{second_str}/'
        '{z}/{x}/{y}.png'
    )
    check_url = (layer.replace('{z}', '0')
                 .replace('{x}', '0')
                 .replace('{y}', '0'))
    response = requests.head(check_url, timeout=10)
    if response.status_code == 200:
        print(f'Updating interferogram: {layer}')
        info_text = html.P([
            f'{first_str}_HH_{second_str}_HH.adf.unw.geo.tif'
            ], style={
                'margin': 0,
                'color': 'rgba(255, 255, 255, 0.9)'
                }
            )
        return layer, info_text
    # else
    print('Layer does not exist')
    raise PreventUpdate


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
    print(f'Loading: {coherence_csv}')
    coherence = _read_coherence(coherence_csv)

    return plot_coherence(coherence)


@callback(
    Output(component_id='coherence-matrix',
           component_property='figure',
           allow_duplicate=True),
    [Input(component_id='tabs-example-graph', component_property='value'),
     Input(component_id='site-dropdown', component_property='value')],
    prevent_initial_call=True
    )
def switch_temporal_view(tab, site):
    """Switch between temporal and spatial baseline plots"""
    if tab == 'tab-1-coherence-graph':
        print(f'coherence for {site}')
        return plot_coherence(_read_coherence(_coherence_csv(site)))
    if tab == 'tab-2-baseline-graph':
        print(f'Baseline for {site}')
        return plot_baseline(_read_baseline(_baseline_csv(site)),
                             _read_coherence(_coherence_csv(site)))
    return None


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
    print(f'Recentering: {coords}')
    info_text = html.P([''], style={
        'margin': 0,
        'color': 'rgba(255, 255, 255, 0.9)'
        })
    return dict(center=coords,
                zoom=10,
                transition="flyTo"), info_text


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
        print("Note: No earthquakes found.")
    base_layers = [
        TileLayer(),
        # generate_controls(overview=False),
        generate_layers_control(),
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
