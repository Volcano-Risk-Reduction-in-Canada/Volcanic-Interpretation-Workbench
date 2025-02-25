#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2024 Government of Canada

Authors:
  - Chloe Lam <chloe.lam@nrcan-rncan.gc.ca>
"""
from dash import html, Input as DashInput, exceptions, Output, ALL, callback, ctx, State as DashState
from datetime import datetime

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


def _text_with_element_in_row(text, component):
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
                        f"Date Range: {log['date_range']}",
                        style=text_styling
                    ),
                    html.P(
                        f"Date Added/Modified: {log['annotation_created']}",
                        style=text_styling
                    )
                ],
                style={**row_element, 'justify-content': 'space-between'}
            ),
            html.P('Observation Notes', style=text_styling),
            html.Div(
                [
                    html.P(log['user']['username'], style=text_styling),
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
    insar_phase_anomalies_values = [
        'Magmatic Deformation' if log and log.get('anomaly_magmatic_deformation') else None,
        'Slope Movement' if log and log.get('anomaly_slope_movement') else None,
        'Glacial Movement' if log and log.get('anomaly_glacial_movement') else None,
        'Topographic Phase Error' if log and log.get('anomaly_topographic_phase_error') else None,
        'Atmospheric Phase Error' if log and log.get('anomaly_atmospheric_phase_error') else None,
        'Baseline Phase Error' if log and log.get('anomaly_baseline_phase_error') else None,
    ]
    # Filter out None values
    insar_phase_anomalies_values = [value for value in insar_phase_anomalies_values if value is not None]
   
    log_user_index = (
        None
        if not log
        else [i for i in range(len(users)) if users[i] == log['user']][0]
    )

    current_date = datetime.today().strftime('%Y-%m-%d')

    return html.Div(
        style={
            'margin': '10px 5px 5px',  # top, left and right, bottom
        },
        children=[
            Store(id='all-users', data=users),
            Store(id='n_clicks_store', data=0),
            html.Div(
                children=[
                    _text_with_element_in_row(
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
                                        [user['username']],
                                        style={
                                            'color': 'black',
                                            'font-size': 15
                                        }
                                    ),
                                    'value': user['username']
                                } for user in users
                            ],
                            value=(
                                users[log_user_index]['username']
                                if log_user_index is not None
                                else ''
                            )
                        )
                    ),
                    html.Div(style={'width': '20px'}),
                    _text_with_element_in_row(
                        'End Date Observed',
                        DatePickerSingle(
                            id='date-picker-single',
                            date=_dict_key_error_check(
                                log,
                                'end_date_observed',
                                current_date  # Use current date as default
                            ),
                            # date=datetime.today().strftime('%Y-%m-%d'),
                            display_format='YYYY-MM-DD',  # Format to display
                            clearable=True,
                            reopen_calendar_on_clear=True,
                        )
                    ),
                    html.Div(style={'width': '20px'}),
                    _text_with_element_in_row(
                        'Date Range',
                        Input(
                            id='date-range',
                            type='number',
                            placeholder='Enter date range',
                            value=_dict_key_error_check(log, 'date_range', 0),
                        )
                    )
                ],
                style=row_element
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            _text_with_element_in_row(
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
                                        'coherence_present',
                                        ''
                                    ),
                                    labelStyle=text_styling
                                )
                            ),
                            _text_with_element_in_row(
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
                            _text_with_element_in_row(
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
                                        'further_interpretation_needed',
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
                                            'interpretation_latitude',
                                            None
                                        ),
                                    ),
                                    Input(
                                        id='longitude',
                                        type='text',
                                        placeholder='Longitude',
                                        value=_dict_key_error_check(
                                            log,
                                            'interpretation_longitude',
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
                                value=insar_phase_anomalies_values,
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
                                        value=['Other'] if log and log.get('anomaly_other') else [],
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
                    _text_with_element_in_row(
                        'Additional Comments',
                        Input(
                            id='my-input',
                            type='text',
                            placeholder='under 100/200 characters',
                            value=_dict_key_error_check(
                                log,
                                'additional_comments',
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
    print(triggered)

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
    Output('observation_log_container', 'children', allow_duplicate=True),
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
        if triggered == 'create-new-annotation-button':
            return observation_log_ui(users, None)
        if isinstance(triggered, dict) and triggered.get('type') == 'annotation-card':
            selected_id = triggered['index']
            print(f"Selected annotation card ID: {selected_id}")
            selected_log = next(
                (log for log in logs if log['id'] == selected_id),
                None
            )
            if selected_log:
                print(f"Selected log: {selected_log}")
            else:
                print("No log found with the selected ID")
            return observation_log_ui(users, selected_log)

    print("No valid trigger, returning default UI")
    return observation_log_ui(users, None)


@callback(
    Output('observation_log_container', 'children', allow_duplicate=True),
    Output('n_clicks_store', 'data'),
    DashInput('submit-update-annotation', 'n_clicks'),
    DashState('n_clicks_store', 'data'),
    DashState('logs-store', 'data'),
    DashState('all-users', 'data'),
    DashState('user-name', 'value'),
    DashState('date-picker-single', 'date'),
    DashState('date-range', 'value'),
    DashState('coherence-present', 'value'),
    DashState('confidence', 'value'),
    DashState('geoscience-interpretation-needed', 'value'),
    DashState('insar-phase-anomalies', 'value'),
    DashState('other-anomaly', 'value'),
    DashState('my-input', 'value'),
    prevent_initial_call=True
)
def submit_update_annotation(n_clicks, prev_n_clicks, logs, users, user_name, date_picker_single, date_range, coherence_present, confidence, geoscience_interpretation_needed, insar_phase_anomalies, other_anomaly, my_input):
    """
    Callback function to submit or update an observation log.
    It listens to click events on the "Submit Annotation" button.
    When triggered, it either creates a new observation log or
    updates an existing observation log based on the form data.

    Parameters:
    n_clicks (int): Click event from the "Submit Annotation" button.
    prev_n_clicks (int): Previous value of n_clicks stored in 'n_clicks_store'.
    logs (list): The current list of observation logs stored in 'logs-store'.
    users (list): List of all users for user selection in the UI.
    user_name (str): The selected user name.
    date_picker_single (str): The selected end date observed.
    date_range (int): The entered date range.
    coherence_present (str): The selected coherence present option.
    confidence (int): The selected confidence value.
    geoscience_interpretation_needed (bool): The selected geoscience interpretation needed option.
    latitude (str): The entered latitude.
    longitude (str): The entered longitude.
    insar_phase_anomalies (list): The selected InSAR phase anomalies.
    other_anomaly (str): The entered other anomaly.
    my_input (str): The entered additional comments.

    Returns:
    tuple: The updated observation log UI and the new value of n_clicks.
    """
    if n_clicks and n_clicks > prev_n_clicks:
        print("submit update button clicked")
        print(f"User: {user_name}")
        print(f"End Date Observed: {date_picker_single}")
        print(f"Date Range: {date_range}")
        print(f"Coherence Present: {coherence_present}")
        print(f"Confidence: {confidence}")
        print(f"Geoscience Interpretation Needed: {geoscience_interpretation_needed}")
        print(f"InSAR Phase Anomalies: {insar_phase_anomalies}")
        print(f"Other Anomaly: {other_anomaly}")
        print(f"Additional Comments: {my_input}")
        data = {
            "end_date_observed": date_picker_single,
            "date_range": date_range,
            "coherence_present": coherence_present,
            "confidence": confidence,
            "further_interpretation_needed": geoscience_interpretation_needed,
            "interpretation_latitude": None,
            "interpretation_longitude": None,
            "anomaly_magmatic_deformation": 'Magmatic Deformation' in insar_phase_anomalies,
            "anomaly_slope_movement": 'Slope Movement' in insar_phase_anomalies,
            "anomaly_glacial_movement": 'Glacial Movement' in insar_phase_anomalies,
            "anomaly_topographic_phase_error": 'Topographic Phase Error' in insar_phase_anomalies,
            "anomaly_atmospheric_phase_error": 'Atmospheric Phase Error' in insar_phase_anomalies,
            "anomaly_baseline_phase_error": 'Baseline Phase Error' in insar_phase_anomalies,
            "anomaly_other": 'Other' in insar_phase_anomalies,
            "insar_phase_anomalies_other": other_anomaly,
            "additional_comments": my_input,
            "user_username": user_name
        }

        # Determine if this is a new annotation or an update
        existing_log = next((log for log in logs if log['user']['username'] == user_name and log['end_date_observed'] == date_picker_single), None)

        if existing_log:
            # Update existing annotation (PUT request)
            url = f"http://your-api-endpoint/{existing_log['id']}"
            response = requests.put(url, json=data)
        else:
            # Create new annotation (POST request)
            url = "http://your-api-endpoint"
            response = requests.post(url, json=data)

        if response.status_code in [200, 201]:
            print("Request successful")
        else:
            print(f"Request failed with status code {response.status_code}")

        # Add your logic here to handle the submission or update
        return observation_log_ui(users, None), n_clicks

    raise exceptions.PreventUpdate

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
