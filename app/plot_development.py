"""
Plot development, meant to be run in jupyter notebook.

This can be deleted once the dash_app has settled down.
"""
# %% setup
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter
from matplotlib.colors import Normalize
from matplotlib.ticker import MultipleLocator

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dash_bootstrap_templates import load_figure_template

COHERENCE_CSV = 'Data/Meager/5M3/CoherenceMatrix.csv'
# COHERENCE_CSV = 'CoherenceMatrixEdgecumbe3M36D.csv'
GROUP_GAP_DAYS = 60
PASS_INTERVAL_DAYS = 12
HEIGHT_INCHES = 3
COH_LIMS = (0.25, 0.65)
CMAP_NAME = 'RdYlBu_r'

CMAP = plt.get_cmap(CMAP_NAME).with_extremes(
    under='blue', over='red', bad='0.2')
NORM = Normalize(*COH_LIMS, clip=False)

plt.style.use('dark_background')
load_figure_template('darkly')

data = pd.read_csv(COHERENCE_CSV, parse_dates=['Reference Date', 'Pair Date'])
data.columns = ['primary', 'secondary', 'coherence']
data['delta_days'] = (data.secondary - data.primary).dt.days

old = data.pivot(index='secondary', columns='primary', values='coherence')

new = data.pivot(index='delta_days', columns='primary', values='coherence')
new = new.loc[~(new.shift().isnull() & new.isnull()).all(axis=1)]
groups = (new.index.to_series().diff() > GROUP_GAP_DAYS).cumsum()
new.loc[0, :] = np.NaN
new.sort_index(inplace=True)


def _ticks_and_spines(ax_list):
    ax_list[0].xaxis.tick_top()
    for above_ax, below_ax in zip(ax_list[:-1], ax_list[1:]):
        above_ax.spines.bottom.set_visible(False)
        above_ax.tick_params(bottom=False)
        below_ax.spines.top.set_visible(False)
        below_ax.tick_params(bottom=False)

    date_locator = AutoDateLocator()
    ax_list[-1].xaxis.set_major_locator(date_locator)
    ax_list[-1].xaxis.set_major_formatter(ConciseDateFormatter(date_locator))


# %% plotly imshow, date vs. date
fig = px.imshow(
    old, x=old.columns, y=old.index, origin='lower',
    color_continuous_scale=CMAP_NAME, range_color=COH_LIMS)

fig.show()
fig.write_image("images/fig1.png")

# %% plotly heatmap, date vs. date
fig = make_subplots(rows=1, cols=1, print_grid=False, shared_yaxes=True)
fig = go.Figure(
    data=go.Heatmap(
        z=old,
        x=old.columns,
        y=old.index,
        colorscale=CMAP_NAME))

fig.show()
fig.write_image("images/fig1.png")

# %% old imshow, date vs. date
fig, ax = plt.subplots(figsize=(8, 8))
im = ax.imshow(
    old, origin='lower',
    extent=(old.columns[0], old.columns[-1],
            old.index[0], old.index[-1]),
    cmap=CMAP, norm=NORM)

locator = AutoDateLocator()
formatter = ConciseDateFormatter(locator)
ax.xaxis.set_major_locator(locator)
ax.xaxis.set_major_formatter(formatter)
ax.yaxis.set_major_locator(locator)
ax.yaxis.set_major_formatter(formatter)

cbar = fig.colorbar(im, ax=ax, label='Coherence', extend='both', shrink=0.5)
cbar.outline.set_color('none')
ax.set_xlabel('Primary')
ax.set_ylabel('Secondary')
fig.show()


# %% plotly heatmap, delta vs. date
heights = [count/groups.value_counts().sum()
           for count in reversed(groups.value_counts())]
fig = make_subplots(
    rows=groups.nunique(), cols=1, shared_xaxes=True,
    vertical_spacing=0.05, row_heights=heights, y_title='Delta [days]')

for group, subset in new.groupby(groups):
    row = int(groups.nunique() - group)
    fig.add_trace(
        go.Heatmap(
            z=subset,
            x=subset.columns,
            y=subset.index,
            coloraxis='coloraxis',
        ),
        row, 1)

fig.update_layout(
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

fig.show()

# %% new imshow, delta vs. date
width_inches = HEIGHT_INCHES*len(new.columns)/groups.value_counts().sum()
height_ratios = list(reversed(groups.value_counts()))

fig, axes = plt.subplots(
    groups.nunique(), 1, sharex=True, squeeze=False,
    figsize=(width_inches, HEIGHT_INCHES), height_ratios=height_ratios)
axes = axes[:, 0]
fig.subplots_adjust(hspace=0.05, right=0.97)
cax = fig.add_axes([0.98, 0.15, 0.02, 0.7])

for ax, (_, subset) in zip(reversed(axes), new.groupby(groups)):
    im = ax.pcolormesh(subset.columns, subset.index, subset,
                       cmap=CMAP, norm=NORM)
    ax.yaxis.set_major_locator(MultipleLocator(PASS_INTERVAL_DAYS))

_ticks_and_spines(axes)

cbar = fig.colorbar(im, cax, ax, label='Coherence', extend='both', shrink=0.5)
cbar.outline.set_color('none')
fig.text(0.04, 0.5, 'Delta [days]', va='center', rotation='vertical')
fig.show()
