#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Chloe Lam <chloe.lam@nrcan-rncan.gc.ca>
"""

from dash import html
from dash_leaflet import (
    TileLayer,
    WMSTileLayer,
    LayersControl,
    BaseLayer,
    Overlay
)

from global_variables import (
    BASEMAP_ATTRIBUTION, 
    BASEMAP_NAME, 
    BASEMAP_URL
)

def generate_layers_control(opacity=0.5):
    """
    Generate a LayersControl object with base layers and overlays.

    Parameters:
    - opacity (float, optional): Opacity level of the WMS overlay layer. Defaults to 0.5.

    Returns:
    - LayersControl: Object containing base layers and overlays for the map.

    Notes:
    - BASEMAP_URL, BASEMAP_ATTRIBUTION, and BASEMAP_NAME should be defined (in global_variables) before calling this function.
    - The function constructs a LayersControl with:
      - One base layer: USGS Topo tile layer.
      - One overlay layer: WMSTileLayer for displaying glacier footprints with specified parameters.
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


def generate_legend(bottom=105):
    # Static legend positioned over the map
    legend = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        style={
                            "background-color": "#e7f5f7",
                            "width": "15px",
                            "height": "15px",
                            "display": "inline-block",
                            "vertical-align": "middle",
                            "margin-right": "5px"
                        }),
                    html.Span(
                        "Glacier",
                        style={
                            "color": "black",
                            "font-size": "12px",
                            "vertical-align": "middle"
                        }
                    )
                ],
                # style={"margin-bottom": "5px"}
            ),
        # Add more legend items as needed
        ],
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
