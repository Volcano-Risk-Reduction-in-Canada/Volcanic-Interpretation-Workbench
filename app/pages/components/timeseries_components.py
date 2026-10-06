#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2026 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>

Timeseries tab: point-target deformation rates as coloured dots on the
site map, and a clicked point's displacement time series in the bottom
pane. Data comes from the site/beam's GeoPackage plus the tiles/stats built
from it by scripts/build_point_tiles.py.
"""
import logging
import os

import dash
from dash import html, callback, Input, Output, State
from dash.dcc import Graph
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from data_utils import (
    _point_tiles,
    has_point_timeseries,
    placeholder_timeseries_figure,
    plot_point_timeseries,
    read_point_stats,
    read_point_timeseries,
)
from global_variables import (
    POINT_DIVERGING_COLORS,
    TEMPORAL_HEIGHT,
    TIMESERIES_BASEMAP,
)

logger = logging.getLogger(__name__)

# 'tabs-example-graph' value for the Timeseries tab.
TIMESERIES_TAB = 'tab-4-timeseries'
DEFAULT_COLOR_VARIABLE = 'rate'
LABEL_STYLE = {'color': 'black', 'font-size': '12px', 'margin': '6px 0 2px'}
CLICK_PROMPT = 'Click a point on the map to plot its displacement time series'


def point_source(target_id):
    """
    MapLibreMap `pointSource` prop for a site/beam, or None if it has no
    point time-series data.
    """
    if not target_id or not has_point_timeseries(target_id):
        return None
    site, beam = target_id.rsplit('_', 1)
    stats = read_point_stats(target_id)
    version = int(os.path.getmtime(_point_tiles(target_id)))
    return {
        'url': (
            f'/getPointTile?site={site}&beam={beam}&v={version}'
            '&z={z}&x={x}&y={y}'
        ),
        'bounds': stats['bounds'],
        'minzoom': stats['minzoom'],
        'maxzoom': stats['maxzoom'],
    }


def _color_stops(lo, hi):
    """
    Value at each of POINT_DIVERGING_COLORS; mirrors pointColorExpression
    in MapLibreMap.react.js so the colourbar matches the map.
    """
    n = len(POINT_DIVERGING_COLORS)
    mid = (n - 1) / 2
    if n % 2 == 1 and lo < 0 < hi:
        return [lo * (1 - i / mid) if i <= mid else hi * ((i - mid) / mid)
                for i in range(n)]
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def _colorbar(lo, hi):
    def pct(value):
        return 100 * (value - lo) / (hi - lo)

    gradient = ', '.join(
        f'{color} {pct(stop):.1f}%'
        for color, stop in zip(POINT_DIVERGING_COLORS, _color_stops(lo, hi))
    )
    tick_style = {'position': 'absolute', 'top': 0, 'font-size': '11px',
                  'color': 'black'}
    ticks = [
        html.Span(f'{lo:g}', style={**tick_style, 'left': 0}),
        html.Span(f'{hi:g}', style={**tick_style, 'right': 0}),
    ]
    if lo < 0 < hi:
        ticks.append(html.Span('0', style={
            **tick_style, 'left': f'{pct(0):.1f}%',
            'transform': 'translateX(-50%)',
        }))
    return [
        html.Div(style={'height': '12px',
                        'background': f'linear-gradient(to right, {gradient})',
                        'border': '1px solid #888'}),
        html.Div(ticks, style={'position': 'relative', 'height': '16px'}),
        html.Div('← subsidence · uplift →',
                 style={'font-size': '11px', 'color': '#555',
                        'text-align': 'center'}),
    ]


def timeseries_tab_layout(target_id):
    """
    Bottom-pane content for the Timeseries tab.

    Parameters:
    - target_id (str): Site/beam id from 'site-dropdown', e.g. 'Meager_5M10'.

    Returns:
    - dash component: colour controls + time-series chart, or a message if
      the site/beam has no point time-series data.
    """
    site, beam = target_id.rsplit('_', 1)
    if not has_point_timeseries(target_id):
        return html.Div(
            [
                html.P(f'No point time-series data for {site} {beam}.'),
                html.P(
                    'Add app/Data/{0}/{1}/{0}_{1}.gpkg and build its tiles '
                    'with: python scripts/build_point_tiles.py --site {0} '
                    '--beam {1}'.format(site, beam),
                    style={'font-size': '12px'}
                ),
            ],
            style={'color': 'black', 'padding': '20px',
                   'height': TEMPORAL_HEIGHT}
        )
    stats = read_point_stats(target_id)
    lo, hi = stats['variables'][DEFAULT_COLOR_VARIABLE]['default_range']
    controls = html.Div(
        [
            html.Div('Colour by', style=LABEL_STYLE),
            dbc.Select(
                id='ts-color-var',
                options=[
                    {'label': f"{v['label']} ({v['units']})", 'value': key}
                    for key, v in stats['variables'].items()
                ],
                value=DEFAULT_COLOR_VARIABLE,
                size='sm',
            ),
            html.Div('Colour range (mm/yr)', style=LABEL_STYLE),
            dbc.InputGroup(
                [
                    dbc.Input(id='ts-range-min', type='number', value=lo,
                              step=1, debounce=True),
                    dbc.InputGroupText('to'),
                    dbc.Input(id='ts-range-max', type='number', value=hi,
                              step=1, debounce=True),
                ],
                size='sm',
            ),
            html.Div(_colorbar(lo, hi), id='ts-colorbar',
                     style={'margin-top': '8px'}),
            html.Div(f"{stats['count']:,} points",
                     style={**LABEL_STYLE, 'color': '#555'}),
        ],
        style={'padding': '0 10px'}
    )
    graph = Graph(
        id='timeseries-graph',
        figure=placeholder_timeseries_figure(CLICK_PROMPT),
        style={'height': TEMPORAL_HEIGHT},
    )
    return dbc.Row([dbc.Col(controls, width=2), dbc.Col(graph, width=10)])


@callback(
    Output('basemap-switcher', 'value'),
    Output('interferogram-bg', 'interferogramVisible'),
    Output('interferogram-bg', 'pointSource'),
    Output('ts-restore', 'data'),
    Input('tabs-example-graph', 'value'),
    Input('site-dropdown', 'value'),
    State('basemap-switcher', 'value'),
    State('ts-restore', 'data'),
    prevent_initial_call=True
)
def toggle_timeseries_mode(tab, site, basemap, restore):
    """
    Put the map in/out of Timeseries mode as that tab is entered/left.

    Entering: remember the current basemap, switch to the greyscale
    hillshade, hide the interferogram, and show the site's points.
    Leaving: put the basemap and interferogram back and drop the points.
    The basemap is changed via the switcher's value (not the map prop
    directly) so the radio buttons stay in sync, through the page's
    basemap-switcher -> activeBasemap callback.

    Parameters:
    - tab (str): Selected tab from 'tabs-example-graph'.
    - site (str): Selected site ID from 'site-dropdown'.
    - basemap (str): Current 'basemap-switcher' value.
    - restore (dict or None): 'ts-restore' store; set while in Timeseries
        mode, holding the basemap to restore on leaving.

    Returns:
    - tuple: basemap-switcher value, interferogramVisible, pointSource, and
        the new 'ts-restore' data.
    """
    if tab == TIMESERIES_TAB:
        if restore:
            # Site changed while already on the tab: swap the points only.
            return (dash.no_update, dash.no_update, point_source(site),
                    dash.no_update)
        return (TIMESERIES_BASEMAP, False, point_source(site),
                {'basemap': basemap})
    if restore:
        return restore['basemap'], True, None, None
    raise PreventUpdate


@callback(
    Output('interferogram-bg', 'pointStyle'),
    Output('ts-colorbar', 'children'),
    Input('ts-color-var', 'value'),
    Input('ts-range-min', 'value'),
    Input('ts-range-max', 'value'),
    # The app defaults to prevent_initial_callbacks; this must also run
    # when the tab's controls first mount, to sync the map with them.
    prevent_initial_call=False
)
def update_point_style(variable, lo, hi):
    """
    Push the colour variable/range to the map's points layer (a paint
    change only -- no tile refetch) and redraw the colourbar to match.
    """
    if variable is None or lo is None or hi is None or lo >= hi:
        raise PreventUpdate
    style = {
        'property': variable,
        'min': lo,
        'max': hi,
        'colors': POINT_DIVERGING_COLORS,
    }
    return style, _colorbar(lo, hi)


@callback(
    Output('ts-range-min', 'value'),
    Output('ts-range-max', 'value'),
    Input('ts-color-var', 'value'),
    State('site-dropdown', 'value'),
    prevent_initial_call=True
)
def reset_range_on_variable_change(variable, target_id):
    """Reset the colour range to the newly chosen variable's default."""
    if not variable or not has_point_timeseries(target_id):
        raise PreventUpdate
    variables = read_point_stats(target_id)['variables']
    lo, hi = variables[variable]['default_range']
    return lo, hi


@callback(
    Output('timeseries-graph', 'figure'),
    Input('interferogram-bg', 'clickedPoint'),
    State('site-dropdown', 'value'),
    prevent_initial_call=True
)
def show_point_timeseries(clicked_point, target_id):
    """Plot the time series of the point clicked on the map."""
    if not clicked_point or clicked_point.get('fid') is None:
        raise PreventUpdate
    fid = clicked_point['fid']
    timeseries = read_point_timeseries(target_id, fid)
    if timeseries is None:
        logger.warning('Point fid %s not found for %s', fid, target_id)
        return placeholder_timeseries_figure(f'Point {fid} not found')
    if len(timeseries['series']) < 2:
        # A few points are 0.0 (i.e. no-data) at every epoch.
        return placeholder_timeseries_figure(
            f'Point {fid} has no valid displacement data'
        )
    return plot_point_timeseries(timeseries)
