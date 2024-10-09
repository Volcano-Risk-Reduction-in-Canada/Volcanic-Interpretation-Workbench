#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

compiles a list of functions that aid in generating
general control functions (LayerControl, Legend, Data Table)

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Chloe Lam <chloe.lam@nrcan-rncan.gc.ca>
"""

import dash
from dash import html, callback
from dash_leaflet import (
    TileLayer,
    WMSTileLayer,
    LayersControl,
    BaseLayer,
    Overlay
)
from dash_extensions.enrich import (Output, Input)

from global_variables import (
    BASEMAP_ATTRIBUTION,
    BASEMAP_NAME,
    BASEMAP_URL,
    LEGEND_BUTTON_STYLING,
    LEGEND_PLACEMENT_STYLING,
    LEGEND_TEXT_STYLING
)


def generate_controls(overview=True, opacity=0.5):
    """
    Generates control components for the dashboard.

    Parameters:
    - overview (bool, optional): Indicates whether to generate controls
        for overview. Defaults to True.
    - opacity (float, optional): Opacity level for (glacier) layers.
        Defaults to 0.5.

    Returns:
    - dash.html.Div: HTML div containing control components
        including legend visibility, data table visibility, and layers control.
    """
    controls = html.Div(
        [
            generate_legend_visibility_control(overview),
            (
                generate_data_table_visibility_control()
                if overview
                else html.Div()
            ),
            generate_layers_control(opacity),
        ]
    )
    return controls


def generate_data_table_visibility_control():
    """
    Generates control for data table visibility.

    Returns:
    - dash.html.Div: HTML div containing a button to
    show/hide data table and a container for data table content.
    """
    data_table_visibility = html.Div(
        [
            html.Button(
                html.H6('Hide Data Table', id='show-data-table-overview'),
                style={**LEGEND_BUTTON_STYLING, "right": "240px"}
            ),
            html.Div(id='data-table-container')
        ]
    )
    return data_table_visibility


def generate_legend_visibility_control(overview):
    """
    Generates control for legend visibility based on overview parameter.

    Parameters:
    - overview (bool): Indicates whether to generate controls
        for overview (True) or site (False).

    Returns:
    - dash.html.Div: HTML div containing buttons to
        show/hide legend and a container for legend content.
    """
    legend_visibility = html.Div(
        [
            html.Button(
                html.H6('Hide Legend', id='show-legend-button-overview'),
                style={**LEGEND_BUTTON_STYLING, "right": "90px"}
            ) if overview else html.Div(),
            html.Button(
                html.H6('Hide Legend', id='show-legend-button-site'),
                style={**LEGEND_BUTTON_STYLING, "right": "90px"}
            ) if not overview else html.Div(),

            html.Div(
                generate_legend(overview=overview),
                id='legend-container',
                style={**LEGEND_PLACEMENT_STYLING, "display": "block"}
            )
        ]
    )
    return legend_visibility


def generate_layers_control(opacity=0.5):
    """
    Generate a LayersControl object with base layers and overlays.

    Parameters:
    - opacity (float, optional): Opacity level of the WMS
        overlay layer. Defaults to 0.5.

    Returns:
    - LayersControl: Object containing base layers and overlays for the map.

    Notes:
    - BASEMAP_URL, BASEMAP_ATTRIBUTION, and BASEMAP_NAME
        should be defined (in global_variables) before calling this function.
    - The function constructs a LayersControl with:
      - One base layer: USGS Topo tile layer.
      - One overlay layer: WMSTileLayer for displaying
        glacier footprints with specified parameters.
    """
    layers_control = LayersControl(
        id='container',
        children=[
            # base layer of the map
            BaseLayer(
                TileLayer(
                    url=BASEMAP_URL,
                    attribution=BASEMAP_ATTRIBUTION
                ),
                name=BASEMAP_NAME,
                checked=True
            ),
            Overlay(
                html.Div([
                    # WMS Layer for Glacier Footprints
                    WMSTileLayer(
                        id='glacier-footprints-wms',
                        url="https://maps.geogratis.gc.ca/wms/canvec_en",
                        layers=(
                            "snow_and_ice_50k,"
                            "snow_and_ice_small,"
                            "snow_and_ice_mid,"
                            "snow_and_ice_large,"
                            "snow_and_ice_250k"
                        ),
                        format="image/png",
                        transparent=True,
                        attribution="Data source: Government of Canada",
                        styles="default",
                        opacity=opacity,
                    ),
                ]),
                name='Glacier Footprints',
                checked=True,
            ),
        ]
    )
    return layers_control


def generate_legend(overview=True):
    """
    Generates a legend with markers and labels.

    Parameters:
    - bottom (int, optional): Distance from the bottom of the
        container in pixels. Default is 30.
    - overview (bool, optional): Indicates whether to generate the legend
        for overview (True) or site (False). Default is True.

    Returns:
    - dash.html.Div: HTML div containing legend items such as glacier,
        volcano, earthquake markers, and InSAR phase change legend.
    """
    # Static legend positioned over the map
    legend_items = [
        get_glacier_markers(),
        get_volcano_markers() if overview else None,
        get_earthquake_markers(),
        get_insar_phase_change() if not overview else None
    ]
    # Filter out None values (markers not included if overview is False)
    legend_items = [item for item in legend_items if item is not None]

    legend = html.Div(
        legend_items,
        # style=LEGEND_PLACEMENT_STYLING(bottom)
        style={
            "background-color": "white",
            "padding": "10px",
            "border": "1px solid #ccc",
            "z-index": "2000"
        }
    )
    return legend


def get_glacier_markers():
    """
    Retrieves Glacier legend label for glacier footprints.

    Returns:
    - dash.html.Div: HTML div containing glacier legend label.
    """
    glacier = html.Div(
        [
            html.H6(
                'Glacier Footprints',
                style={**LEGEND_TEXT_STYLING, "fontWeight": "bold"}
            ),
            html.Div(
                style={
                    "background-color": "#e7f5f7",
                    "width": "15px",
                    "height": "15px",
                    "display": "inline-block",
                    "vertical-align": "middle",
                    "margin-right": "5px"
                }
            ),
            html.Span(
                "Glacier",
                style=LEGEND_TEXT_STYLING
            )
        ],
        style={"margin-bottom": "5px"}
    )
    return glacier


def get_volcano_markers(icon_width=15):
    """
    Retrieves content for volcano legend label.

    Parameters:
    - icon_width (int, optional): Width of the volcano icon.
        Default is 15 pixels.

    Returns:
    - dash.html.Div: HTML div containing volcano legend label.
    """
    icon_styling = {
        "width": f"{icon_width}px",
        "height": "auto",
        "margin-right": "5px"
    }
    red_icon = html.Img(
        src=dash.get_asset_url('red_volcano_transparent.png'),
        style=icon_styling
    )
    green_icon = html.Img(
        src=dash.get_asset_url('green_volcano_transparent.png'),
        style=icon_styling
    )
    volcano = html.Div(
        [
            html.H6(
                'Volcanoes',
                style={**LEGEND_TEXT_STYLING, "fontWeight": "bold"}
            ),
            html.Div([
                red_icon,
                html.Span(
                    "Unrest Observed",
                    style=LEGEND_TEXT_STYLING
                ),
            ]),
            html.Div([
                green_icon,
                html.Span(
                    "No Unrest Observed",
                    style=LEGEND_TEXT_STYLING
                )
            ])
        ],
        style={"margin-bottom": "5px"}
    )
    return volcano


def get_earthquake_markers():
    """
    Retrieves content for earthquake legend label.

    Returns:
    - dash.html.Div: HTML div containing earthquake legend label.
    """
    age_colors = [
        # RED
        {
            'rgba': 'rgba(255, 0, 0, 0.6)',
            'age': 'Day'
        },
        # ORANGE
        {
            'rgba': 'rgba(255, 165, 0, 0.6)',
            'age': 'Week'
        },
        # YELLOW
        {
            'rgba': 'rgba(255, 255, 0, 0.6)',
            'age': 'Month'
        },
        # WHITE
        {
            'rgba': 'rgba(255, 255, 255, 0.6)',
            'age': 'Older'
        }
    ]
    magnitudes = [1, 2, 3, 4, 5, 6, 7]
    magnitude_markers = []
    age_markers = []

    for magnitude in magnitudes:
        comparison_operator = ""
        if magnitude == 1:
            comparison_operator = "\u2264 "
        elif magnitude == 7:
            comparison_operator = "\u2265 "

        magnitude_div = html.Div([
            html.Div([
                html.Div([
                    html.Div(
                        style={
                            "width": f"{magnitude * 6}px",
                            "height": f"{magnitude * 6}px",
                            "borderRadius": "50%",
                            "border": "0.5px solid black",
                            "backgroundColor": 'white',
                            "marginRight": "5px",
                        }
                    ),
                    html.Span(
                        f"{comparison_operator}{magnitude}",
                        style={
                            **LEGEND_TEXT_STYLING,
                            "display": "inline-block",
                            "verticalAlign": "middle",  # Align text vertically
                            "width": "35px"
                        }
                    ),
                ], style={
                    "display": "flex",
                    "alignItems": "center",
                }),
            ], style={
                "width": "44px",
                "display": "flex",
                "justifyContent": "center",  # Center horizontally
                "alignItems": "center",
            }),
        ], style={"display": "block", "margin": "5px 10px"})
        magnitude_markers.append(magnitude_div)
    for color in age_colors:
        age_div = html.Div([
            html.Div(
                style={
                    "background-color": color['rgba'],
                    "width": "15px",
                    "height": "15px",
                    "display": "inline-block",
                    "vertical-align": "middle",
                    "border": "0.5px solid black",
                    "margin-right": "5px",
                }
            ),
            html.Span(
                f"{color['age'].capitalize()}",
                style=LEGEND_TEXT_STYLING
            ),
        ])
        age_markers.append(age_div)
    earthquake_styling = {
        "display": "inline-block",
        "verticalAlign": "top"
    }

    earthquake = html.Div(
        [
            html.H6(
                'Earthquakes',
                style={**LEGEND_TEXT_STYLING, "fontWeight": "bold"}
            ),
            html.Div(
                [
                    html.H6(
                        'Age (Past)',
                        style={**LEGEND_TEXT_STYLING, "fontWeight": "bold"}
                    ),
                ] + age_markers,
                style={**earthquake_styling, "marginRight": "10px"}),
            html.Div(
                [
                    html.H6(
                        'Magnitude',
                        style={**LEGEND_TEXT_STYLING, "fontWeight": "bold"}
                    ),
                ] + magnitude_markers,
                style={**earthquake_styling, "marginLeft": "10px"})
        ],
        style={"margin-bottom": "5px"}
    )
    return earthquake


def get_insar_phase_change():
    """
    Retrieves content for InSAR phase change legend label.

    Returns:
    - dash.html.Div: HTML div containing InSAR phase change legend label.
    """
    # Define RGBA colors
    colors_rgba = [
        'rgba(0,191,169,255)',
        'rgba(0,60,248,255)',
        'rgba(102,0,234,255)',
        'rgba(217,0,133,255)',
        'rgba(255,0,0,255)',
        'rgba(212,142,0,255)',
        'rgba(98,236,0,255)',
        'rgba(0,253,35,255)',
        'rgba(0,191,169,255)',
    ]
    labels = [
        {'position': '0%', 'label': '-\u03C0'},
        {'position': '50%', 'label': '0'},
        {'position': '100%', 'label': '\u03C0'}
    ]
    # Join colors into linear gradient format
    gradient_colors = ', '.join(colors_rgba)

    insar_phase_change = html.Div(
        [
            html.H6(
                'InSAR Phase Change',
                style={**LEGEND_TEXT_STYLING, "fontWeight": "bold"}
            ),
            html.Div(
                style={
                    "position": "relative",
                    "width": "100%",
                    "height": "10px",
                    "background": (
                        f"linear-gradient(to right, "
                        f"{gradient_colors}"
                    )
                },
                children=[
                    html.Div(
                        style={
                            "position": "absolute",
                            "bottom": "-30px",
                            "left": f"{label['position']}",
                            "textAlign": "center",
                            "color": "white"
                        },
                        children=[
                            html.Div(
                                style={
                                    "width": "1px",
                                    "height": "10px",
                                    "background": 'black',
                                    "margin": "0 auto",
                                    "marginLeft": "-1px",
                                    "marginTop": "5px"
                                }
                            ),
                            html.Span(
                                f"{label['label']}",
                                style={
                                    **LEGEND_TEXT_STYLING,
                                    "marginLeft": "-3px",
                                    "verticalAlign": "middle"
                                },
                            ),
                        ]
                    )
                    for label in labels
                ]
            )
        ],
        style={"margin-bottom": "20px"}
    )
    return insar_phase_change


@callback(
    [
        Output('legend-container', 'style', allow_duplicate=True),
        Output('show-legend-button-overview', 'children')
    ],
    [Input('show-legend-button-overview', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_legend_visibility_overview(n_clicks):
    """
    Callback to toggle the visibility of the legend
    for OVERVIEW and update the button text.

    Parameters:
    - n_clicks (int or None): Number of times the button
    'show-legend-button-overview' has been clicked.

    Returns:
    - tuple: A tuple containing:
      - dash.html.Div: HTML content to update
      the legend container ('legend-container').
      - str: Updated text for the 'show-legend-button-overview' button.
    """
    if n_clicks is None:
        return dash.no_update, dash.no_update
    # Toggle visibility based on odd/even clicks
    show_legend = n_clicks % 2 == 0
    button_text = 'Hide Legend' if show_legend else 'Show Legend'

    return {
        **LEGEND_PLACEMENT_STYLING,
        "display": "block" if show_legend else "none"
    }, button_text


@callback(
    [
        Output('legend-container', 'style', allow_duplicate=True),
        Output('show-legend-button-site', 'children')
    ],
    [Input('show-legend-button-site', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_legend_visibility_site(n_clicks):
    """
    Callback to toggle the visibility of the legend for
    SITE and update the button text.

    Parameters:
    - n_clicks (int or None): Number of times the button
        'show-legend-button-site' has been clicked.

    Returns:
    - tuple: A tuple containing:
      - dash.html.Div: HTML content to update the
        legend container ('legend-container').
      - str: Updated text for the 'show-legend-button-site' button.
    """
    if n_clicks is None:
        return dash.no_update, dash.no_update
    # Toggle visibility based on odd/even clicks
    show_legend = n_clicks % 2 == 0
    button_text = 'Hide Legend' if show_legend else 'Show Legend'

    return {
        **LEGEND_PLACEMENT_STYLING,
        "display": "block" if show_legend else "none"
    }, button_text


@callback(
    [
        Output('data-table-container', 'style'),
        Output('show-data-table-overview', 'children')
    ],
    [Input('show-data-table-overview', 'n_clicks')],
)
def toggle_data_table_visibility(n_clicks):
    """
    Callback to toggle the visibility of the data table for
    overview and update the button text.

    Parameters:
    - n_clicks (int or None): Number of times the button
        'show-data-table-overview' has been clicked.

    Returns:
    - tuple: A tuple containing:
      - dict: CSS style dictionary to update the
        'data-table-container' display property.
      - str: Updated text for the 'show-data-table-overview' button.
    """
    if n_clicks is None:
        return dash.no_update, dash.no_update
    # Toggle visibility based on odd/even clicks
    show_table = n_clicks % 2 == 0
    button_text = 'Hide Data Table' if show_table else 'Show Data Table'
    return {"display": "block" if show_table else "none"}, button_text
