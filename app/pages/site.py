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
import configparser
import json
import requests

import dash
import numpy as np
import pandas as pd

from dash import html, callback
from dash.dcc import Graph, Tab, Tabs
from dash_bootstrap_templates import load_figure_template
import dash_bootstrap_components as dbc
from dash_leaflet import Map, TileLayer, LayersControl, BaseLayer, WMSTileLayer
from dash_extensions.enrich import (Output,
                                    DashProxy,
                                    Input,
                                    MultiplexerTransform)

from plotly.graph_objects import Heatmap
from plotly.subplots import make_subplots
import plotly.graph_objects as go

dash.register_page(__name__, path='/site')


def get_config_params(args):
    """Parse configuration from supplied file."""
    config_obj = configparser.ConfigParser()
    config_obj.read(args)
    return config_obj


def _read_coherence(coherence_csv):
    if coherence_csv is None:
        return None
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


def _read_baseline(baseline_csv):
    if baseline_csv is None:
        return None
    baseline = pd.read_csv(
        baseline_csv,
        delimiter=' ',
        header=None,
        skipinitialspace=True)
    baseline.columns = ['index',
                        'first_date',
                        'second_date',
                        'bperp',
                        'btemp',
                        'bperp2',
                        'x']
    baseline = baseline.drop(['index',
                              'btemp',
                              'bperp2',
                              'x'], axis=1)
    baseline['first_date'] = pd.to_datetime(baseline['first_date'],
                                            format="%Y%m%d")
    baseline['second_date'] = pd.to_datetime(baseline['second_date'],
                                             format="%Y%m%d")
    return baseline


def _valid_dates(coh):
    return coh.first_date.dropna().unique()


def _coherence_csv(target_id):
    if target_id == 'API Response Error':
        return None
    site, beam = target_id.rsplit('_', 1)
    return f'app/Data/{site}/{beam}/CoherenceMatrix.csv'


def _baseline_csv(target_id):
    if target_id == 'API Response Error':
        return None
    site, beam = target_id.rsplit('_', 1)
    return f'app/Data/{site}/{beam}/bperp_all'


def pivot_and_clean(coh_long):
    """Convert long-form coherence to wide-form and clean it up."""
    coh_wide = coh_long.pivot(
        index='delta_days',
        columns='second_date',
        values='coherence')
    # include zero baseline even though it will never be valid
    coh_wide.loc[0, :] = np.NaN
    coh_wide.sort_index(inplace=True)
    # because hovertemplate 'f' format doesn't handle NaN properly
    coh_wide = coh_wide.round(2)
    # trim empty edges
    coh_wide = coh_wide.loc[
        (coh_wide.index >= 0) &
        (coh_wide.index <= coh_wide.max(axis='columns').last_valid_index()),
        (coh_wide.columns >= coh_wide.max(axis='index').first_valid_index()) &
        (coh_wide.columns <= coh_wide.max(axis='index').last_valid_index())]
    return coh_wide


def pivot_and_clean_dates(coh_long, coh_wide):
    """Convert long-form df to wide-form date matrix matching coh_wide."""
    coh_long = coh_long.drop(coh_long[coh_long.second_date <
                                      coh_long.first_date].index)
    date_wide = coh_long.pivot(
        index='delta_days',
        columns='second_date',
        values='first_date')
    date_wide = date_wide.applymap(lambda x: pd.to_datetime(x)
                                   .strftime('%b %d, %Y') if x is not pd.NaT
                                   else x)
    # remove some columns so that date_wide has
    # the same columns as coh_wide
    common_cols = [col for col in
                   set(date_wide.columns).intersection(coh_wide.columns)]
    common_cols.sort()
    date_wide = date_wide[common_cols]
    # date_wide.drop(columns=date_wide.columns[0], axis=1,  inplace=True)
    return date_wide


def plot_coherence(coh_long):
    """Plot coherence for different baselines as a function of time."""
    if coh_long is None:
        fig = make_subplots(
            rows=YEAR_AXES_COUNT, cols=1, shared_xaxes=True,
            start_cell='bottom-left', vertical_spacing=0.02,
            y_title='Temporal baseline [days]')
        return fig
    coh_long['delta_days'] = (coh_long.second_date -
                              coh_long.first_date).dt.days
    coh_wide = pivot_and_clean(coh_long)
    date_wide = pivot_and_clean_dates(coh_long, coh_wide)

    fig = make_subplots(
        rows=YEAR_AXES_COUNT, cols=1, shared_xaxes=True,
        start_cell='bottom-left', vertical_spacing=0.02,
        y_title='Temporal baseline [days]')

    for year in range(YEAR_AXES_COUNT):
        fig.add_trace(
            trace=Heatmap(
                z=coh_wide.values,
                x=coh_wide.columns,
                y=coh_wide.index,
                xgap=1,
                ygap=1,
                customdata=date_wide,
                hovertemplate=(
                    'Start Date: %{customdata}<br>'
                    'End Date: %{x}<br>'
                    'Temporal Baseline: %{y} days<br>'
                    'Coherence: %{z}'),
                coloraxis='coloraxis'),
            row=year + 1, col=1)
        if year == 0:
            baseline_limits = [0, BASELINE_MAX]
        else:
            baseline_limits = list(int(year*DAYS_PER_YEAR) +
                                   BASELINE_MAX/2*np.array([-1, 1]))
        second_date_limits = [
            max(coh_wide.columns.min(),
                coh_wide.columns.max() -
                pd.to_timedelta(DAYS_PER_YEAR*MAX_YEARS, 'days')) -
            pd.to_timedelta(4, 'days'),
            coh_wide.columns.max() + pd.to_timedelta(4, 'days')]
        fig.update_yaxes(
            range=baseline_limits,
            dtick=BASELINE_DTICK,
            scaleanchor='x',
            row=year + 1, col=1)
        fig.update_xaxes(
            range=second_date_limits,
            row=year + 1, col=1)

    fig.update_layout(
        margin={'l': 65, 'r': 0, 't': 5, 'b': 5},
        coloraxis={
            'colorscale': CMAP_NAME,
            'cmin': COH_LIMS[0],
            'cmax': COH_LIMS[1],
            'colorbar': {
                'title': 'Coherence',
                'dtick': 0.1,
                'ticks': 'outside',
                'tickcolor': 'white',
                'thickness': 20,
            }},
        showlegend=False)

    return fig


def plot_baseline(df_baseline, df_cohfull):
    """Plot perpendicular baseline as a function of time."""
    if df_baseline is None or df_cohfull is None:
        bperp_combined_fig = go.Figure()
        return bperp_combined_fig
    # if :
    #     bperp_combined_fig = go.Figure()
    #     return bperp_combined_fig
    bperp_scatter_fig = go.Scatter(x=df_baseline['second_date'],
                                   y=df_baseline['bperp'],
                                   mode='markers')
    df_baseline_edge = df_cohfull[df_cohfull['coherence'].notna()]
    df_baseline_edge = df_baseline_edge.drop(columns=['coherence'])
    df_baseline_edge = pd.merge(df_baseline_edge,
                                df_baseline[['second_date', 'bperp']],
                                right_on='second_date',
                                left_on='first_date',
                                how='left')
    df_baseline_edge = df_baseline_edge.drop(columns=['second_date_y'])
    df_baseline_edge = \
        df_baseline_edge.rename(columns={"second_date_x": "second_date",
                                         "bperp": "bperp_reference_date"})
    df_baseline_edge = pd.merge(df_baseline_edge,
                                df_baseline[['second_date', 'bperp']],
                                right_on='second_date',
                                left_on='second_date',
                                how='left')

    df_baseline_edge = df_baseline_edge.rename(
        columns={"bperp": "bperp_pair_date"})
    df_baseline_edge = df_baseline_edge[
        df_baseline_edge['bperp_reference_date'].notna()]

    edge_x = []
    edge_y = []

    for _, edge in df_baseline_edge.iterrows():
        edge_x.append(edge['first_date'])
        edge_x.append(edge['second_date'])
        edge_y.append(edge['bperp_reference_date'])
        edge_y.append(edge['bperp_pair_date'])

    bperp_line_fig = go.Scatter(x=edge_x, y=edge_y,
                                line=dict(width=0.5, color='#888'),
                                mode='lines')

    bperp_combined_fig = go.Figure(data=[bperp_line_fig, bperp_scatter_fig])
    bperp_combined_fig.update_layout(yaxis_title="Perpendicular Baseline (m)",
                                     margin={'l': 65, 'r': 0, 't': 5, 'b': 5})
    bperp_combined_fig.update(layout_showlegend=False)

    return bperp_combined_fig


def populate_beam_selector(vrrc_api_ip):
    """creat dict of site_beams and centroid coordinates"""
    beam_response_dict = get_api_response(vrrc_api_ip, 'beams')
    targets_response_dict = get_api_response(vrrc_api_ip, 'targets')
    beam_dict = {}
    for beam in beam_response_dict:
        try:
            beam_string = beam['short_name']
            for target in targets_response_dict:
                if target['label'] == beam['target_label']:
                    matching_target = target
            site_string = matching_target['name_en']
            site_beam_string = f'{site_string}_{beam_string}'
            target_coordinates = matching_target['geometry']['coordinates'][0]
            centroid_x, centroid_y = calc_polygon_centroid(target_coordinates)
            beam_dict[site_beam_string] = [centroid_y, centroid_x]
        except TypeError:
            beam_dict['API Response Error'] = [50.64, -123.60]
    return beam_dict


def get_api_response(vrrc_api_ip, route):
    """Get a response from the vrrc API given an ip and a route"""
    try:
        response = requests.get(f'http://{vrrc_api_ip}/{route}/',
                                timeout=10)
        response.raise_for_status()
        response_dict = json.loads(response.text)
        return response_dict
    except requests.exceptions.RequestException as exception:
        response_dict = {}
        response_dict['API Response Error'] = [exception.args[0]]
        return response_dict


def calc_polygon_centroid(coordinates):
    """Calculate centroid from geojson coordinates"""
    # Extract the coordinates
    x_coords = [point[0] for point in coordinates]
    y_coords = [point[1] for point in coordinates]
    # Calculate the centroid
    centroid_x = sum(x_coords) / len(coordinates)
    centroid_y = sum(y_coords) / len(coordinates)
    return round(centroid_x, 2), round(centroid_y, 2)


config = get_config_params('config.ini')

# TODO add support for some or all of the following parameters to config

# dashboard configuration
TEMPLATE = 'darkly'
TITLE = 'Volcano InSAR Interpretation Workbench'

# basemap configuration
BASEMAP_URL = (
    'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer'
    '/tile/{z}/{y}/{x}')
BASEMAP_ATTRIBUTION = (
    'Tiles courtesy of the '
    '<a href="https://usgs.gov/">U.S. Geological Survey</a>')
BASEMAP_NAME = 'USGS Topo'

# coherence plotting configuration
YEAR_AXES_COUNT = 1
BASELINE_MAX = 150
BASELINE_DTICK = 24
YEARS_MAX = 5
CMAP_NAME = 'RdBu_r'
COH_LIMS = (0.2, 0.4)
TEMPORAL_HEIGHT = 300
MAX_YEARS = 3
DAYS_PER_YEAR = 365.25


# construct dashboard
load_figure_template('darkly')
# app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app = DashProxy(prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()],
                external_stylesheets=[dbc.themes.DARKLY])

TILES_BUCKET = config.get('AWS', 'tiles')
TARGET_CENTRES_INI = populate_beam_selector(config.get('API', 'vrrc_api_ip'))
TARGET_CENTRES = {i: TARGET_CENTRES_INI[i] for i in sorted(TARGET_CENTRES_INI)}
INITIAL_TARGET = 'Meager_5M3'
INITIAL_TARGET_SPLIT = INITIAL_TARGET.split('_')
SITE_INI = INITIAL_TARGET_SPLIT[0]
BEAM_INI = INITIAL_TARGET_SPLIT[1]

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
        TileLayer(
            id='tiles',
            url=(
                f'{TILES_BUCKET}/{SITE_INI}/{BEAM_INI}/20220821_20220914/'
                '{z}/{x}/{y}.png'
            ),
            maxZoom=20,
            minZoom=1,
            attribution='&copy; Open Street Map Contributors',
            tms=True,
            opacity=0.7)
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

    TARGET_SPLIT = target_id.split('_')
    SITE = TARGET_SPLIT[0]
    BEAM = TARGET_SPLIT[1]

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
    print(f'Updating interferogram: {layer}')
    return layer


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
    return dict(center=coords,
                zoom=10,
                transition="flyTo")


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

