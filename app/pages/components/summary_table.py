#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2024 Government of Canada

Authors:
  - Chloe Lam <chloe.lam@nrcan-rncan.gc.ca>
"""

from dash import dash_table


def summary_table_ui(summary_table_df):
    """
    Generates a Dash DataTable for displaying a
    summary table with conditional styling.

    This function takes a DataFrame containing summary
    data and returns a Dash DataTable UI component.
    The table displays the columns from the DataFrame
    and applies conditional color styling based on the "Unrest" column.
    If the value in the "Unrest" column is True,
    the corresponding row text color is red; otherwise, it is green.

    Parameters:
    ----------
    summary_table_df : pandas.DataFrame
        A DataFrame containing the summary data to be displayed
        in the table. It is expected to have at least a 'Unrest'
        column for conditional styling.

    Returns:
    -------
    dash_table.DataTable
        A Dash DataTable component displaying the summary data
        with conditional row styling based on the "Unrest" column.
    """
    return dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in summary_table_df.columns],
        data=summary_table_df.to_dict('records'),
        style_table={'color': 'black'},
        style_cell={'textAlign': 'left'},
        style_data_conditional=[
            {
                'if': {'column_id': 'Unrest', 'row_index': i},
                'color': 'red' if unrest else 'green',
            }
            for i, unrest in enumerate(summary_table_df['Unrest'])
        ],
    )
