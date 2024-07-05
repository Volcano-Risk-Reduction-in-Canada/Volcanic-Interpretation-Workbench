#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Chloe Lam <chloe.lam@nrcan-rncan.gc.ca>
"""

import dash
from dash import html
from dash_leaflet import (
    TileLayer,
    WMSTileLayer,
    LayersControl,
    BaseLayer,
    Overlay,
    CircleMarker
)

from global_variables import (
    BASEMAP_ATTRIBUTION,
    BASEMAP_NAME,
    BASEMAP_URL,
    LEGEND_TEXT_STYLING
)


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
    LAYERS_CONTROL = LayersControl(
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
            )
        ] +
        [
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
    return LAYERS_CONTROL


def generate_legend(bottom=105, overview=True):
    # Static legend positioned over the map
    legend_items = [
        get_glacier_markers(),
        get_volcano_markers() if overview else None,
        get_earthquake_markers() if overview else None,
        # Add more legend items as needed
    ]
    # Filter out None values (markers not included if overview is False)
    legend_items = [item for item in legend_items if item is not None]
    
    legend = html.Div(
        legend_items,
        style={
            "position": "absolute",
            "bottom": f"{bottom}px",
            "right": "12px",
            "background-color": "white",
            "padding": "10px",
            "border": "1px solid #ccc",
            "z-index": "1000"
        }
    )
    return legend


def get_glacier_markers():
    glacier = html.Div(
        [
            html.H6('Glacier Footprints', style={**LEGEND_TEXT_STYLING, "fontWeight": "bold"}),
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
    icon_styling ={
        "width":f"{icon_width}px",
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
            html.H6('Volcanoes', style={**LEGEND_TEXT_STYLING, "fontWeight": "bold"}),
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
    age_colors = [
        # RED
        {
            'rgba': 'rgba(255, 0, 0, 0.6)',
            'age': '2 Days'
        },
        # ORANGE
        {
            'rgba': 'rgba(255, 165, 0, 0.6)',
            'age': 'Week'
        },
        # YELLOW
        {
            'rgba': 'rgba(255, 255, 0, 0.6)',
            'age': 'month'
        },
        # WHITE
        {
            'rgba': 'rgba(255, 255, 255, 0.6)',
            'age':'older'
        }
    ]
    magnitudes = [1,2,3,4,5,6,7]
    
    magnitude_markers = []
    age_markers = []

    for magnitude in magnitudes:
        comparison_operator = ""
        if magnitude == 1: comparison_operator = f"\u2264 "
        elif magnitude == 7: comparison_operator = f"\u2265 "

        magnitude_div = html.Div([
            html.Div(
                style={
                    "width": f"{magnitude * 3 + 3}px",
                    "height": f"{magnitude * 3 + 3}px",
                    "display": "inline-block",
                    "vertical-align": "middle",
                    "borderRadius": "50%",
                    "border": "0.5px solid black",
                    "backgroundColor": 'white',
                    "marginRight": "5px"
                }
            ),
            html.Span(
                f"{comparison_operator}{magnitude}",
                style=LEGEND_TEXT_STYLING
            ),
        ])
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
                    "margin-right": "5px"
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
    age_markers_div = html.Div(age_markers, style={**earthquake_styling, "marginRight": "10px"})
    magnitude_markers_div = html.Div(magnitude_markers, style={**earthquake_styling, "marginLeft": "10px"})
    earthquake = html.Div(
        [
            html.H6('Earthquakes', style={**LEGEND_TEXT_STYLING, "fontWeight": "bold"}),
            age_markers_div,
            magnitude_markers_div
        ],
        style={"margin-bottom": "5px"}
    )
    return earthquake