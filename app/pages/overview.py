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
import logging
from dash import html, dcc, callback
from dash_leaflet import (
    Map,
    CircleMarker,
    Popup,
)
from dash_extensions.enrich import (Output, Input)
from dash_extensions.javascript import (assign)

from pages.components.summary_table import summary_table_ui
from pages.components.gc_header import gc_header
from global_components import generate_controls
from data_utils import (
    build_summary_table,
    get_green_volcanoes,
    get_latest_quakes_chis_fsdn,
    get_red_volcanoes,
    read_targets_geojson,
)

logger = logging.getLogger(__name__)

dash.register_page(__name__, path='/')

# VARIABLES
markers_red = get_red_volcanoes()
markers_green = get_green_volcanoes()
epicenters_df = get_latest_quakes_chis_fsdn()

initial_show_glacier_information = False

on_each_feature = assign("""function(feature, layer, context){
    layer.bindTooltip(`${feature.properties.name_en}`)
}""")

summary_table_df = build_summary_table(read_targets_geojson())

# LAYOUT
layout = html.Div(
    style={
        # 'height': '100vh',
        'display': 'flex',
        'flexDirection': 'column',
        'topMargin': 5,
        'bottomMargin': 5,
        'justifyContent': 'center',
        'alignItems': 'flex-start',
        'background-color': 'white'
    },
    children=[  # All children should be in this list
        dcc.Location(id='url', refresh=True),
        # Hidden div for triggering callback (for page reload)
        html.Div(id='trigger-reload', style={'display': 'none'}),
        dcc.Store(id='selected_feature'),
        # HEADER
        gc_header('VRRC InSAR National Overview'),
        # MAP
        html.Div(
            id='overview_map',
            style={
                'width': '98%',
                'height': '90vh',
                'position': 'relative',
                'margin': '0 auto',
            },
            children=[
                Map(
                    id='map',
                    style={'width': '100%', 'height': '88vh'},

                    center=[54.64, -123.60],
                    zoom=6,
                    children=[
                        # base layer of map + additional controls
                        generate_controls(),
                        # red and green volcano markers
                        *markers_green,
                        *markers_red,
                        # circle markers (earthquakes) populated in callback
                        html.Div(id='circle-marker'),
                    ]
                ),
            ]
        ),
        # TABLE (on top right corner)
        html.Div(
            html.Div(
                id='table-container',
                style={
                    'position': 'absolute',
                    'top': '165px',
                    'right': '25px',
                    'width': '480px',
                    'zIndex': 1000
                },
                children=summary_table_ui(summary_table_df)
            ),
            id="data-table-container",
            style={"display": "block"}
        )
    ]
)


"""
    Callback to update map data on page reload.
    INPUT: hidden div in Layout with ID 'trigger-reload'
    OUTPUT: various circle markers, generated from the updated map data
"""


@callback(
    Output('circle-marker', 'children'),
    [Input('trigger-reload', 'children')]
)
def update_map_data(_):
    """
        Call get_latest_quakes_chis_fsdn() on page reload.
        Generate and return circle markers for each data
        point (representing an earthquake)
    """
    # get the most updated data and assign it to epicenters_df
    epicenters_df = get_latest_quakes_chis_fsdn()

    circle_markers = [
        CircleMarker(
            center=[row['Latitude'], row['Longitude']],
            radius=3*row['Magnitude'],
            fillColor=row['quake_colour'],
            fillOpacity=0.6,
            color='black',
            weight=1,
            # information about the earthquake (as a popup)
            children=Popup(
                html.P(
                    [f"""Magnitude: {row['Magnitude']} \
                                    {row['MagType']}""",
                     html.Br(),
                     f"Date: {row['Time'][0:10]}",
                     html.Br(),
                     f"Depth: {row['Depth/km']} km",
                     html.Br(),
                     f"EventID: {row['#EventID']}",
                     html.Br(),
                     ])),
        )
        for _, row in epicenters_df.sort_values(
            by='#EventID').iterrows()
    ]

    # updated data
    return circle_markers


"""
    Callback to navigate to the site page about
    the specific red or green volcano clicked.
    INPUT: any of the green or red volcanos
    OUTPUT: the url changes to '/site'
"""


@callback(
    Output('url', 'pathname', allow_duplicate=True),
    [[Input(
        component_id=i.id,
        component_property='n_clicks') for i in markers_green],
     [Input(
         component_id=i.id,
         component_property='n_clicks') for i in markers_red]],
    prevent_initial_call=True,
    suppress_callback_exceptions=True
)
def navigate_to_site_page(*args):
    """
        Navigate to the site detail page
        anytime a red or green marker is clicked
    """
    ctx = dash.callback_context
    logger.info("CTX: %s, %s",
                type(ctx),
                args)
    return '/site'


@callback(
    Output('table-container', 'children'),
    Input('url', 'href')  # This triggers the callback when the page reloads
)
def update_summary_table(_):
    # Dynamically build the summary table each time the page is loaded
    summary_table_df = build_summary_table(read_targets_geojson())
    # Return the updated table
    return summary_table_ui(summary_table_df)
