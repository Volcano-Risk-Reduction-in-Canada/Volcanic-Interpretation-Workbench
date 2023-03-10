#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
  - Nick Ackerley <nicholas.ackerley@nrcan-rncan.gc.ca>
"""
import configparser

import numpy as np
import pandas as pd

from dash import Dash, html
from dash.dcc import Graph, Dropdown
from dash.dependencies import Input, Output
from dash_bootstrap_templates import load_figure_template
from dash_bootstrap_components import themes
from dash_leaflet import Map, TileLayer, LayersControl, BaseLayer, WMSTileLayer

from plotly.graph_objects import Heatmap
from plotly.subplots import make_subplots


def get_config_params(args):
    """Parse configuration from supplied file."""
    config_obj = configparser.ConfigParser()
    config_obj.read(args)
    return config_obj


config = get_config_params('config.ini')
GEOSERVER_ENDPOINT = config.get('geoserver', 'geoserverEndpoint')

# TODO add support for some or all of the following parameters to config

# dashboard configuration
TEMPLATE = 'darkly'
TITLE = 'Volcano InSAR Interpretation Workbench'
INITIAL_TARGET = 'Meager_5M3'

# basemap configuration
BASEMAP_URL = (
    'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer'
    '/tile/{z}/{y}/{x}')
BASEMAP_ATTRIBUTION = (
    'Tiles courtesy of the '
    '<a href="https://usgs.gov/">U.S. Geological Survey</a>')
BASEMAP_NAME = 'USGS Topo'

# coherence plotting configuration
GROUP_GAP_DAYS = 60
CMAP_NAME = 'plasma'
COH_LIMS = (0.2, 0.5)

# TODO read target configuration from database
TARGET_CENTRES = {
    'Meager_5M2': [50.64, -123.60],
    'Meager_5M3': [50.64, -123.60],
    'Meager_5M8': [50.64, -123.60],
    'Meager_5M10': [50.64, -123.60],
    'Meager_5M15': [50.64, -123.60],
    'Meager_5M21': [50.64, -123.60],
    'Garibaldi_3M6': [49.90, -122.99],
    'Garibaldi_3M7': [49.90, -122.99],
    'Garibaldi_3M18': [49.90, -122.99],
    'Garibaldi_3M23': [49.90, -122.99],
    'Garibaldi_3M30': [49.90, -122.99],
    'Garibaldi_3M34': [49.90, -122.99],
    'Garibaldi_3M42': [49.90, -122.99],
    'Cayley': [50.12, -123.29],
    'Cayley_3M1': [50.12, -123.29],
    'Cayley_3M6': [50.12, -123.29],
    'Cayley_3M13': [50.12, -123.29],
    'Cayley_3M14': [50.12, -123.29],
    'Cayley_3M17': [50.12, -123.29],
    'Cayley_3M24': [50.12, -123.29],
    'Cayley_3M30': [50.12, -123.29],
    'Cayley_3M36': [50.12, -123.29],
    'Edgecumbe_3M36D': [50.05, -135.75],
    'Edziza_North_3M13': [57.74, -130.64],
    'Edziza_North_3M41': [57.74, -130.64],
    'Edziza_South_3M12': [57.64, -130.64],
    'Edziza_South_3M31': [57.64, -130.64],
    'Edziza_South_3M42': [57.64, -130.64],
    'Tseax_3M7': [55.11, -128.90],
    'Tseax_3M9': [55.11, -128.90],
    'Tseax_ 3M19': [55.11, -128.90],
    'Tseax_3M40': [55.11, -128.90],
    'Nazko_3M9': [52.93, -123.73],
    'Nazko_3M20': [52.93, -123.73],
    'Nazko_3M31': [52.93, -123.73],
    'Hoodoo_3M8': [56.77, -131.29],
    'Hoodoo_3M11': [56.77, -131.29],
    'Hoodoo_3M14': [56.77, -131.29],
    'Hoodoo_3M38': [56.77, -131.29],
    'Hoodoo_3M41': [56.77, -131.29],
    'LavaFork_3M11': [56.42, -130.85],
    'LavaFork_3M20': [56.42, -130.85],
    'LavaFork_3M21': [56.42, -130.85],
    'LavaFork_3M29': [56.42, -130.85],
    'LavaFork_3M31': [56.42, -130.85],
    'LavaFork_3M41': [56.42, -130.85],
}

# could this be handled instead with a style sheet?
LR_MARGIN_PX = 10
TB_MARGIN_PX = 5


def _read_coherence(coherence_csv):
    coh = pd.read_csv(
        coherence_csv,
        parse_dates=['Reference Date', 'Pair Date'])
    coh.columns = ['first_date', 'second_date', 'coherence']
    wrong_order = (coh.second_date < coh.first_date) & coh.coherence.notnull()
    if wrong_order.any():
        raise RuntimeError(
            'Some intereferogram dates not ordered as expected:\n' +
            coh[wrong_order].to_string())
    return coh


def _valid_dates(coh):
    return coh.first_date.dropna().unique()


def _coherence_csv(target_id):
    site, beam = target_id.split('_', 1)
    return f'Data/{site}/{beam}/CoherenceMatrix.csv'


def _plot_coherence(coh_long):
    coh_long['delta_days'] = (coh_long.second_date -
                              coh_long.first_date).dt.days
    coh_wide = coh_long.pivot(
        index='delta_days',
        columns='second_date',
        values='coherence')

    # because hovertemplate 'f' format doesn't handle NaN properly
    coh_wide = coh_wide.round(2)

    coh_wide = coh_wide.loc[~(coh_wide.shift().isnull() &
                              coh_wide.isnull()).all(axis=1)]
    groups = (coh_wide.index.to_series().diff() > GROUP_GAP_DAYS).cumsum()
    coh_wide.loc[0, :] = np.NaN
    coh_wide.sort_index(inplace=True)

    heights = [count/groups.value_counts().sum()
               for count in reversed(groups.value_counts())]
    fig = make_subplots(
        rows=groups.nunique(), cols=1, shared_xaxes=True,
        vertical_spacing=0.05, row_heights=heights,
        y_title='Temporal baseline [days]')

    for group, subset in coh_wide.groupby(groups):
        row = int(groups.nunique() - group)
        fig.add_trace(
            Heatmap(
                z=subset.values,
                x=subset.columns,
                y=subset.index,
                hovertemplate=(
                    'Second: %{x}<br>'
                    'First: -%{y} days<br>'
                    'Coherence: %{z}'),
                coloraxis='coloraxis',
            ),
            row, 1)

    fig.update_layout(
        margin={
            'l': LR_MARGIN_PX + 60,
            'r': LR_MARGIN_PX,
            't': TB_MARGIN_PX,
            'b': TB_MARGIN_PX},
        coloraxis={
            'colorscale': CMAP_NAME,
            'cmin': COH_LIMS[0],
            'cmax': COH_LIMS[1],
            'colorbar': {
                'title': 'Coherence',
                'dtick': 0.1,
                'ticks': 'outside',
                'tickcolor': 'white',
            },
        },
        showlegend=False)
    return fig


# construct dashboard
load_figure_template('darkly')
app = Dash(__name__, external_stylesheets=[themes.DARKLY])
app.layout = html.Div(
    id='parent',

    children=[

        html.Div(
            children=[
                html.Label('Target_Beam:'),
                Dropdown(
                    id='site-dropdown',
                    options=list(TARGET_CENTRES.keys()),
                    value=INITIAL_TARGET,
                    style={
                        'color': 'black',
                        'width': 200
                    })],
            style={
                'marginLeft': LR_MARGIN_PX,
                'marginRight': LR_MARGIN_PX,
                'marginTop': TB_MARGIN_PX,
                'marginBottom': TB_MARGIN_PX,
            },
            title=TITLE,
            ),

        html.Div(
            children=[
                Map([
                    TileLayer(),
                    LayersControl(
                        BaseLayer(
                            TileLayer(
                                url=BASEMAP_URL,
                                attribution=BASEMAP_ATTRIBUTION
                            ),
                            name=BASEMAP_NAME,
                            checked=True
                        ),
                    ),
                    WMSTileLayer(
                        id='interferogram',
                        url=f'{GEOSERVER_ENDPOINT}/{INITIAL_TARGET}/wms?',
                        layers='cite:20210717_HH_20210903_HH.adf.wrp.geo',
                        format='image/png',
                        transparent=True,
                        opacity=0.75),
                    WMSTileLayer(
                        url=f'{GEOSERVER_ENDPOINT}/vectorLayers/wms?',
                        layers='cite:permanent_snow_and_ice_2',
                        format='image/png',
                        transparent=True,
                        opacity=1.0)],
                    id='interferogram-bg',
                    center=TARGET_CENTRES[INITIAL_TARGET],
                    zoom=12,
                    style={
                        'height': '60%',
                    }),
                Graph(
                    id='coherence-matrix',
                    figure=_plot_coherence(
                        _read_coherence(_coherence_csv(INITIAL_TARGET))),
                    style={
                        'height': '40%',
                    }),
            ],
            style={
                'height': 800,
                'marginLeft': LR_MARGIN_PX,
                'marginRight': LR_MARGIN_PX,
            }
        ),

        # html.Div(
        #     Map([
        #         TileLayer(),
        #         LayersControl(
        #             BaseLayer(
        #                 TileLayer(
        #                     url=BASEMAP_URL,
        #                     attribution=BASEMAP_ATTRIBUTION
        #                 ),
        #                 name=BASEMAP_NAME,
        #                 checked=True
        #             ),
        #         ),
        #         WMSTileLayer(
        #             id='intensity-map',
        #             url=f'{GEOSERVER_ENDPOINT}/{INITIAL_TARGET}/wms?',
        #             layers='cite:20210114_HH.rmli.geo.db',
        #             format='image/png',
        #             transparent=True,
        #             opacity=1.0),
        #         ],
        #         id='intensity-background',
        #         center=[50.64, -123.6],
        #         zoom=12,
        #     ),
        #     style={
        #         'width': '96%',
        #         'height': '550px',
        #         'display': 'inline-block'}
        #     ),
        # html.Div([
        #     Slider(
        #         min=0,
        #         max=len(_valid_dates(coherence)),
        #         step=1,
        #         marks={
        #             i: _valid_dates(coherence)[i] for i in range(
        #                 0, len(_valid_dates(coherence)), 10)},
        #         value=0,
        #         id='date-slider'),
        #     html.Div(id='date-display')
        # ]),
        # html.Div(),
    ]
)


@app.callback(
    Output(component_id='interferogram', component_property='layers'),
    Input(component_id='coherence-matrix', component_property='clickData'))
def update_interferogram(click_data):
    """Update interferogram display."""
    if not click_data:
        return 'cite:20210717_HH_20210903_HH.adf.wrp.geo'
    second = pd.to_datetime(click_data['points'][0]['x'])
    delta = pd.Timedelta(click_data['points'][0]['y'], 'days')
    first = second - delta

    first_str = first.strftime('%Y%m%d')
    second_str = second.strftime('%Y%m%d')
    layer = f'cite:{first_str}_HH_{second_str}_HH.adf.wrp.geo'
    print(f'Updating interferogram: {layer}')
    return layer


@app.callback(
    Output(component_id='interferogram', component_property='url'),
    Input(component_id='site-dropdown', component_property='value'))
def update_site(value):
    """Switch between sites."""
    url = f'{GEOSERVER_ENDPOINT}/{value}/wms?'
    print(f'New site url: {url}')
    return url


@app.callback(
    Output(component_id='coherence-matrix', component_property='figure'),
    Input(component_id='site-dropdown', component_property='value'))
def update_coherence(target_id):
    """Display new coherence matrix."""
    coherence_csv = _coherence_csv(target_id)
    print(f'Loading: {coherence_csv}')
    coherence = _read_coherence(coherence_csv)

    return _plot_coherence(coherence)


@app.callback(
    Output(component_id='interferogram-bg', component_property='center'),
    Input(component_id='site-dropdown', component_property='value'))
def recenter_map(target_id):
    """Center map on new site."""
    coords = TARGET_CENTRES[target_id]
    print(f'Recentering: {coords}')
    return coords


# @app.callback(
#     Output('date-display', 'children'),
#     Input('date-slider', 'value'))
# def update_output(value):
#     """Update backscatter date text."""
#     date = _valid_dates(coherence)[value]
#     title = f'Date: "{date}"'
#     print(f'Slider title: {title}')
#     return title


# @app.callback(
#     Output('intensity-map', 'layers'),
#     Input('date-slider', 'value'))
# def update_intensity(value):
#     """Update backscatter image on map"""
#     date = _valid_dates(coherence)[value]
#     date = date.replace('-', '')
#     layers = f'cite:{date}_HH.rmli.geo.db'
#     print(f'Updating backscatter: {layers}')
#     return layers


if __name__ == '__main__':
    # TODO login and set up - or at least test - port forwarding
    # See https://shorturl.at/lnSY1
    app.run_server(host='0.0.0.0', port=8050, debug=True)
