#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2024 Government of Canada

Authors:
  - Chloe Lam <chloe.lam@nrcan-rncan.gc.ca>
"""
from dash import html, Input as DashInput, Output, ALL, callback, ctx

from dash.dcc import (
    Dropdown,
    Input,
    RadioItems,
    Slider,
    Checklist,
    DatePickerSingle,
    Store
)

from global_styling import (
    title_text_styling,
    text_styling,
    row_element,
    button_style,
    annotation_card_style,
    triangle_style
)

# #######################################################
# LOCAL variables used throughout this file

insar_phase_anomalies = [
    'Magmatic Deformation',
    'Slope Movement',
    'Glacial Movement',
    'Topographic Phase Error',
    'Atmospheric Phase Error',
    'Baseline Phase Error',
]

SELECTED_ANNOTATION_COLOUR = 'red'

# ######################################################
#  HELPER Components


def _dict_key_error_check(dict, key, none_value):
    return dict[key] if dict and key in dict else none_value


def _textWithElementInRow(text, component):
    return html.Div(
        [
            html.P(text, style=title_text_styling),
            component
        ],
        style=row_element
    )


def _annotations_card(log):
    return html.Button(
        id={'type': 'annotation-card', 'index': log['id']},
        children=[
            html.Div(
                id={'type': "annotation-triangle", 'index': log['id']},
                style={**triangle_style, 'display': 'none'}
            ),
            html.Div(
                [
                    html.P(
                        f"Date Range: {log['dateRange']}",
                        style=text_styling
                    ),
                    html.P(
                        f"Date Added/Modified: {log['dateAddedModified']}",
                        style=text_styling
                    )
                ],
                style={**row_element, 'justify-content': 'space-between'}
            ),
            html.P('Observation Notes', style=text_styling),
            html.Div(
                [
                    html.P(log['user']['name'], style=text_styling),
                    html.P(log['user']['email'], style=text_styling)
                ],
                style={**row_element, 'justify-content': 'space-between'}
            ),
        ],
        style=annotation_card_style,
        n_clicks=0
    )


# ####################################################
#  MAIN List of Logs UI
def logs_list_ui(logs, width):
    """
    Creates the UI layout for displaying a list of observation logs.

    This function generates a vertical list of previously created observation
    logs, each displayed as a card with relevant information.
    It also provides a button to create a new annotation.

    Parameters:
    ----------
    logs : list
        A list of dictionaries where each dictionary represents a log
        or annotation with relevant details (e.g., 'id', 'endDateObserved').
    width : int or float
        The percentage width (relative to its container)
        that this UI component should occupy.

    Returns:
    --------
    html.Div
        A Dash HTML Div containing the UI layout, including a list of
        previous logs, a button to create a new annotation,
        and a scrollable container to handle larger lists of logs.
    """
    return html.Div(
        style={
            'borderLeft': '5px solid black',  # Black border on the left side,
            'width': f'{width}%'
        },
        children=[
            Store(id='logs-store', data=logs),
            html.H5(
                'Previous Annotations (End Date: )',
                style={**title_text_styling, 'margin': '10px 5px'}
            ),
            html.Div(
                [
                    _annotations_card(
                        log
                    ) for log in logs
                ],
                style={
                    'height': '70%',
                    'overflowY': 'auto',
                }
            ),
            html.Div(
                [
                    html.Button(
                        'Create New Annotation',
                        id='create-new-annotation-button',
                        style={
                            **button_style,
                            'margin': '1px 10px',
                        }
                    ),
                ],
                n_clicks=0,
                style={'display': 'flex', 'justify-content': 'flex-end'}
            ),
        ]
    )


#  MAIN Observation Log UI Screen
def observation_log_ui(users, log=None):
    """
    Creates the main observation log UI layout.

    This function builds the observation log interface based on the
    provided users and an optional log data. If a log is provided,
    the fields will be pre-populated with the log's data; otherwise,
    the fields are set to default values. It includes components
    for user selection, date entry, coherence, confidence,
    geoscience interpretation, and InSAR phase anomalies.

    Parameters:
    ----------
    users : list
        A list of user dictionaries where each dictionary contains user details
        (e.g., 'name', 'id').
    log : dict, optional
        The observation log data used to populate the form fields.
        If `None`, the form will be empty (default is `None`).

    Returns:
    --------
    html.Div
        A Dash HTML Div containing the entire UI layout for observation logs,
        including user selection, date input, anomaly selection,
        and submission buttons.
    """
    coherence_present_options = ['Yes', 'No', 'Unsure, need a second opinion']
    log_user_index = (
        None
        if not log
        else [i for i in range(len(users)) if users[i] == log['user']][0]
    )
    return html.Div(
        style={
            'margin': '10px 5px 5px',  # top, left and right, bottom
        },
        children=[
            Store(id='all-users', data=users),
            html.Div(
                children=[
                    _textWithElementInRow(
                        'User',
                        Dropdown(
                            id='user-name',
                            placeholder='Select a User',
                            style={
                                'width': '180px'
                            },
                            options=[
                                {
                                    'label': html.Span(
                                        [user['name']],
                                        style={
                                            'color': 'black',
                                            'font-size': 15
                                        }
                                    ),
                                    'value': user['name']
                                } for user in users
                            ],
                            value=(
                                users[log_user_index]['name']
                                if log_user_index
                                else ''
                            )
                        )
                    ),
                    html.Div(style={'width': '20px'}),
                    _textWithElementInRow(
                        'End Date Observed',
                        DatePickerSingle(
                            id='date-picker-single',
                            date=_dict_key_error_check(
                                log,
                                'endDateObserved',
                                ''
                            ),
                            display_format='YYYY-MM-DD',  # Format to display
                            clearable=True,
                            reopen_calendar_on_clear=True,
                        )
                    ),
                    html.Div(style={'width': '20px'}),
                    _textWithElementInRow(
                        'Date Range',
                        Input(
                            # id='date-range',
                            type='number',
                            placeholder='Enter date range',
                            value=_dict_key_error_check(log, 'dateRange', 0),
                        )
                    )
                ],
                style=row_element
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            _textWithElementInRow(
                                'Coherence Present',
                                RadioItems(
                                    id='coherence-present',
                                    options=[
                                        {
                                            'label': option,
                                            'value': option
                                        }
                                        for option in coherence_present_options
                                    ],
                                    inline=True,
                                    value=_dict_key_error_check(
                                        log,
                                        'coherencePresent',
                                        ''
                                    ),
                                    labelStyle=text_styling
                                )
                            ),
                            _textWithElementInRow(
                                'Confidence',
                                html.Div(
                                    [
                                        Slider(
                                            id='confidence',
                                            min=0,
                                            max=100,
                                            step=1,
                                            marks={
                                                i: str(i)
                                                for i in range(0, 101, 10)
                                            },
                                            value=_dict_key_error_check(
                                                log,
                                                'confidence',
                                                0
                                            ),
                                        )
                                    ],
                                    style={"width": '400px'}
                                )
                            ),
                            _textWithElementInRow(
                                'Further Geoscience Interpretation Needed',
                                RadioItems(
                                    id='geoscience-interpretation-needed',
                                    options=[
                                        {'label': 'Yes', 'value': True},
                                        {'label': 'No', 'value': False},
                                    ],
                                    inline=True,
                                    labelStyle=text_styling,
                                    value=_dict_key_error_check(
                                        log,
                                        'furtherInterpretationNeeded',
                                        None
                                    ),
                                )
                            ),
                            html.Div(
                                children=[
                                    Input(
                                        id='latitude',
                                        type='text',
                                        placeholder='Latitude',
                                        value=_dict_key_error_check(
                                            log,
                                            'interpretationLatitude',
                                            None
                                        ),
                                    ),
                                    Input(
                                        id='longitude',
                                        type='text',
                                        placeholder='Longitude',
                                        value=_dict_key_error_check(
                                            log,
                                            'interpretationLongitude',
                                            None
                                        ),
                                    ),
                                ],
                                style={'margin-left': '10px'},
                                id='lat-long-interpretation'
                            )
                        ],
                        style={
                            'display': 'flex',
                            'flex-direction': 'column',
                            'align-content': 'space-around',
                            'row-gap': '10px'
                        }
                    ),
                    html.Div(
                        children=[
                            html.P(
                                'InSAR Phase Anomalies',
                                style=title_text_styling
                            ),
                            Checklist(
                                id='insar-phase-anomalies',
                                options=[
                                    {
                                        'label': anomaly,
                                        'value': anomaly
                                    } for anomaly in insar_phase_anomalies
                                ],
                                value=_dict_key_error_check(
                                    log,
                                    'insarPhaseAnomalies',
                                    []
                                ),
                                labelStyle=text_styling
                            ),
                            html.Div(
                                children=[
                                    Checklist(
                                        id='other-checkbox',
                                        options=[{
                                            'label': 'Other',
                                            'value': 'Other'
                                        }],
                                        value=_dict_key_error_check(
                                            log,
                                            'insarPhaseAnomalies',
                                            []
                                        ),
                                        labelStyle=text_styling,
                                        inline=True
                                    ),
                                    Input(
                                        id='other-anomaly',
                                        type='text',
                                        placeholder='Enter Anomaly',
                                        style={
                                            'marginLeft': '10px',
                                            'width': '200px',
                                        },
                                        value=_dict_key_error_check(
                                            log,
                                            'insarPhaseAnomaliesOther',
                                            ''
                                        )
                                    )
                                ],
                                style=row_element
                            )
                        ],
                        style={
                            'width': '30vw',
                            'margin-right': '12vw',
                            'justify-content': 'flex-end'
                        }
                    )
                ],
                style={**row_element, 'justify-content': 'flex-start'}
            ),
            html.Div(
                children=[
                    _textWithElementInRow(
                        'Additional Comments',
                        Input(
                            id='my-input',
                            type='text',
                            placeholder='under 100/200 characters',
                            value=_dict_key_error_check(
                                log,
                                'additionalComments',
                                ''
                            )
                        )
                    ),
                    html.Button(
                        f"{'Update' if log else 'Submit'} Annotation",
                        id='submit-update-annotation',
                        style=button_style
                    ),
                ],
                style={
                    **row_element,
                    'justify-content': 'space-between',
                    'align-items': 'flex-end'
                }
            )
        ]
    )


# Callback to update the selected log
@callback(
    [
        Output({"type": "annotation-triangle", "index": ALL}, 'style'),
        Output({"type": "annotation-card", "index": ALL}, 'style'),
    ],
    [
        DashInput({'type': 'annotation-card', 'index': ALL}, 'n_clicks'),
        DashInput('create-new-annotation-button', 'n_clicks')
    ],
    [DashInput('logs-store', 'data')],
    prevent_initial_call=True
)
def update_card_styles(clicks, new_clicks, logs):
    """
    Callback function to update the styles of annotation cards and triangles
    based on user interactions. It updates the background color of the selected
    annotation card and displays the associated triangle indicator.

    Parameters:
    clicks (list): List of click events from annotation cards.
    new_clicks (int): Click event from the "create new annotation" button.
    logs (list): The current list of observation logs stored in 'logs-store'.

    Returns:
    tuple: A list of style dictionaries for the annotation triangles and a
    list of style dictionaries for the annotation cards, reflecting the
    selected log or a new log creation.
    """
    # Find which button was clicked
    triggered = ctx.triggered_id if ctx.triggered_id else None

    if 'create-new-annotation-button' in triggered:
        return (
            [{**triangle_style} for _ in logs],
            [{**annotation_card_style} for _ in logs]
        )
    if 'annotation-card' in triggered['type']:
        index = triggered.get('index') if triggered else None

        # Update styles based on selection
        return (
            [
                {
                    **triangle_style,
                    'display': 'block' if log['id'] == index else 'none'
                }
                for log in logs
            ],
            [
                {
                    **annotation_card_style,
                    'background-color': (
                        SELECTED_ANNOTATION_COLOUR
                        if log['id'] == index
                        else 'white'
                    )
                }
                for log in logs
            ]
        )
    return None  # Default return if no valid trigger


@callback(
    Output('observation_log_container', 'children'),
    [
        DashInput({'type': 'annotation-card', 'index': ALL}, 'n_clicks'),
        DashInput('create-new-annotation-button', 'n_clicks')
    ],
    [DashInput('logs-store', 'data')],
    DashInput('all-users', 'data'),
    prevent_initial_call=True
)
def update_observation_log_ui(clicks, new_clicks, logs, users):
    """
    Callback function to update the observation log UI.
    It listens to click events on annotation cards or
    the "create new annotation" button.
    When triggered, it either creates a new observation log UI
    or loads an existing observation log based on the
    selected annotation.

    Parameters:
    clicks (list): List of click events from annotation cards.
    new_clicks (int): Click event from the "create new annotation" button.
    logs (list): The current list of observation logs stored in 'logs-store'.
    users (list): List of all users for user selection in the UI.

    Returns:
    Component or None: The updated observation log UI based on
    the interaction, or None if no valid trigger occurs.
    """
    triggered = ctx.triggered_id
    if triggered:
        if 'create-new-annotation-button' in triggered:
            return observation_log_ui(users, None)
        if 'annotation-card' in triggered['type']:
            selected_id = triggered['index']
            selected_log = next(
                (log for log in logs if log['id'] == selected_id),
                None
            )
            return observation_log_ui(users, selected_log)

    return None  # Default return if no valid trigger


@callback(
    Output('lat-long-interpretation', 'style'),
    DashInput('geoscience-interpretation-needed', 'value')
)
def toggle_lat_long_visibility(geoscience_interpretation_needed):
    """
    Toggle the visibility of the latitude and longitude input fields
    based on the value of the 'further geoscience interpretation
    needed' radio button.

    Parameters:
    geoscience_interpretation_needed: bool
        The value selected for 'further geoscience interpretation needed'.
        If True, the latitude and longitude fields are shown.
        If False, they are hidden.

    Returns:
    dict: CSS styles to control the visibility of the latitude
    and longitude fields.
        {'display': 'block'} to show the fields,
        {'display': 'none'} to hide them.
    """
    # Check if the value is 'Yes', and return a visible style, else hide it
    if geoscience_interpretation_needed:
        # Show the lat-long section
        return {'margin-left': '10px', 'display': 'block'}
    return {'display': 'none'}  # Hide the lat-long section

# TODO: create a callback that clears lat/long fields when no is selected
# TODO: create a callback that will create a new log or update the current log
