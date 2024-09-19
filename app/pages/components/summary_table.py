from dash import dash_table


def summary_table_ui(summary_table_df):
    return dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in summary_table_df.columns],
        data=summary_table_df.to_dict('records'),
        style_table={'color': 'black'},
        style_data_conditional=[
            {
                'if': {'column_id': 'Unrest', 'row_index': i},
                'color': 'red' if unrest else 'green',
            }
            for i, unrest in enumerate(summary_table_df['Unrest'])
        ],
    )
