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

selected_annotation_colour = 'red'

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

def _annotationsCard(log):
    return html.Button(
        id={'type': 'annotation-card', 'index': log['id']},
        children=[
            html.Div(id={'type': "annotation-triangle", 'index': log['id']}, style={**triangle_style, 'display': 'none'}), 
            html.Div(
                [
                    html.P(f'Date Range: {log['dateRange']}', style=text_styling),
                    html.P(f'Date Added/Modified: {log['dateAddedModified']}', style=text_styling)
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
    cleaned_logs = [log[0] if isinstance(log, tuple) else log for log in logs]
    print(cleaned_logs)
    return html.Div(
        style={
            'borderLeft': '5px solid black',  # Black border on the left side,
            'width': f'{width}%'
        },
        children=[
            Store(id='logs-store', data=cleaned_logs),
            html.H5('Previous Annotations (End Date: )', style={**title_text_styling, 'margin': '10px 5px'}),
            html.Div(
                [
                    _annotationsCard(
                        log
                    ) for log in cleaned_logs
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
                            'margin': '5px 15px', # top and bottom, left and right
                        }
                    ),
                ],
                n_clicks=0, 
                style={ 'display': 'flex', 'justify-content': 'flex-end' }
            ),
        ]
    )
#  MAIN Observation Log UI Screen

def observation_log_ui(users, log=None):
    coherencePresentOptions = ['Yes', 'No','Unsure, need a second opinion']
    logUserIndex = None if not log else [i for i in range(len(users)) if users[i] == log['user']][0]
    print(logUserIndex, users)
    return html.Div(
        style={
            'margin': '10px 5px 5px', # top, left and right, bottom
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
                                'width' : '180px'
                            },
                            options=[
                                {
                                    'label': html.Span(
                                        [user['name']], 
                                        style={'color': 'black', 'font-size': 15}
                                    ),
                                    'value': user['name']
                                } for user in users
                            ],
                            value=users[logUserIndex]['name'] if logUserIndex else ''
                            # value=users[logUserIndex] if logUserIndex else ''
                        )
                    ),
                    html.Div(style={'width':'20px'}),
                    _textWithElementInRow(
                        'End Date Observed',
                        DatePickerSingle(
                            id='date-picker-single',
                            date=_dict_key_error_check(log, 'endDateObserved', ''),
                            display_format='YYYY-MM-DD',  # Format to display
                            clearable=True,
                            reopen_calendar_on_clear=True,
                        )
                    ),
                    html.Div(style={'width':'20px'}),
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
                                        {'label': option, 'value': option} for option in coherencePresentOptions
                                    ],
                                    inline=True,
                                    value=_dict_key_error_check(log, 'coherencePresent', ''),
                                    labelStyle=text_styling
                                )
                            ),
                            _textWithElementInRow(
                                'Confidence',
                                html.Div(
                                    [
                                        Slider(
                                            id='confidence',
                                            min=0,            # Minimum value of the slider
                                            max=100,          # Maximum value of the slider
                                            step=1,           # Step size
                                            marks={i: str(i) for i in range(0, 101, 10)},  # Marks on the slider
                                            value=_dict_key_error_check(log, 'confidence', 0),
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
                                    value=_dict_key_error_check(log, 'furtherGeoscienceInterpretationNeeded', None),
                                )
                            ),
                            html.Div(
                                children=[
                                    Input(
                                        id='latitude',
                                        type='text',
                                        placeholder='Latitude',
                                        value=_dict_key_error_check(log, 'interpretationLatitude', None),
                                    ),
                                    Input(
                                        id='longitude',
                                        type='text',
                                        placeholder='Longitude',
                                        value=_dict_key_error_check(log, 'interpretationLongitude', None),
                                    ),
                                ],
                                style={'margin-left': '10px'}
                            )
                        ],
                        style={
                            'display': 'flex',
                            'flex-direction': 'column',
                            'align-content': 'space-around',
                            'row-gap': '10px'
                        }
                    ),
                    html.Div(style={'width': '20vw', 'height': '100%', 'background-color': 'purple'}),
                    html.Div(
                        children=[
                            html.P('InSAR Phase Anomalies', style=title_text_styling),
                            Checklist(
                                id='insar-phase-anomalies',
                                options=[
                                    {'label': anomaly, 'value': anomaly} for anomaly in insar_phase_anomalies
                                ],
                                value=log['insarPhaseAnomalies'] if log != None else [],
                                labelStyle=text_styling
                            ),
                            html.Div(
                                children=[
                                    Checklist(
                                        id='other-checkbox',
                                        options=[{'label': 'Other', 'value': 'Other'}],
                                        value=log['insarPhaseAnomalies'] if log != None else [],
                                        labelStyle=text_styling
                                    ),
                                    Input(
                                        id='other-anomaly',
                                        type='text',
                                        placeholder='Enter Anomaly',
                                        style={
                                            'marginLeft': '10px', 
                                            'width': '200px', 
                                        },
                                        value=log['insarPhaseAnomaliesOther'] if log != None and 'insarPhaseAnomaliesOther' in log else ''
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
                            value=log['additionalComments'] if log != None else ''
                        )
                    ),
                    html.Button(
                        f'{'Update' if log else 'Submit'} Annotation',
                        id='submit-update-annotation',
                        style=button_style
                    ),
                ],
                style={**row_element, 'justify-content': 'space-between', 'align-items': 'flex-end'}
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
def update_card_styles(annotation_clicks, new_annotation_clicks, logs):
    # Find which button was clicked
    triggered = ctx.triggered_id if ctx.triggered_id else None

    if 'create-new-annotation-button' in triggered:
        return (
            [
                {**triangle_style} for _ in logs
            ],
            [
                {**annotation_card_style} for _ in logs
            ] 
        )
    elif 'annotation-card' in triggered['type']:
        index = triggered.get('index') if triggered else None

        # Update styles based on selection
        return (
            [
                {**triangle_style, 'display': 'block' if log['id'] == index else 'none'}
                for log in logs
            ],
            [
                {**annotation_card_style, 'background-color': selected_annotation_colour if log['id'] == index else 'white'}
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
def update_observation_log_ui(annotation_clicks, new_annotation_clicks, logs, users):
    triggered = ctx.triggered_id
    if triggered:
        if 'create-new-annotation-button' in triggered:
            return observation_log_ui(users, None)
        elif 'annotation-card' in triggered['type']:
            selected_id = triggered['index']
            selected_log = next((log for log in logs if log['id'] == selected_id), None)
            return observation_log_ui(users, selected_log)
    
    return None  # Default return if no valid trigger


# TODO: create a callback that will create a new log or update the current log