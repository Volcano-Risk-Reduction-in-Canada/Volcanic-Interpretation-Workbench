#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Chloe Lam <chloe.lam@nrcan-rncan.gc.ca>
"""


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

def generate_layers_control():
    LAYERS_CONTROL = LayersControl(
                [
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
                            opacity=0.5,
                        ),
                        name='Glacier Footprints',
                        checked=True
                    )
                ]
            )
    return LAYERS_CONTROL