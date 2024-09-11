from dash import html
from dash.dcc import Dropdown, Input, RadioItems, Slider, Checklist, DatePickerSingle
from global_styling import title_text_styling, text_styling, row_element, button_style

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

# ######################################################
#  HELPER Components

def _textWithElementInRow(text, component):
    return html.Div(
        [
            html.P(text, style=title_text_styling),
            component
        ],
        style=row_element
    )

def _annotationsCard(selected=False):
    # Define the triangle style
    triangle_style = {
        'position': 'absolute',
        'width': '0',
        'height': '0',
        'border-top': '10px solid transparent',
        'border-bottom': '10px solid transparent',
        'border-right': '10px solid black',  # Color of the triangle
        'left': '-10px',  # Position the triangle to the left
        'top': '50%',  # Center vertically
        'transform': 'translateY(-50%)'  # Adjust vertical alignment
    }
    # Container style
    container_style = {
        'border': '2px solid black',
        'padding': '10px',
        'margin': '10px',
        'position': 'relative',  # Ensure container is positioned relatively
        'padding-left': '20px'  # Make space for the triangle
    }

    return html.Div(
        [
            html.Div(style=triangle_style) if selected else None,  # Add triangle if selected,
            html.Div(
                [
                    html.P('Date Range', style=text_styling),
                    html.P('Date Added/Modified', style=text_styling)
                ],
                style={**row_element, 'justify-content': 'space-between'}
            ),
            html.P('Observation Notes', style=text_styling),
            html.Div(
                [
                    html.P('Observer A', style=text_styling),
                    html.P('observerA@email.com', style=text_styling)
                ],
                style={**row_element, 'justify-content': 'space-between'}
            ),
        ],
        style=container_style
    )

# ####################################################
#  MAIN Observation Log UI Screen

def observation_log_ui():
    return html.Div(
        style={
            'display': 'flex',
            'flexDirection': 'row',
            'alignItems': 'stretch',
           'backgroundColor': 'white',
           'margin': '20px 10px',
           'height': '35vh'
        },
        children=[
            html.Div(
                style={
                    'width': '70%',
                    'margin': '10px 5px 5px', # top, left and right, bottom
                },
                children=[
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
                                        {'label': html.Span(['User 1'], style={'color': 'black', 'font-size': 15}), 'value': 'user1'},
                                        {'label': html.Span(['User 2'], style={'color': 'black', 'font-size': 15}), 'value': 'user2'},
                                        {'label': html.Span(['User 3'], style={'color': 'black', 'font-size': 15}), 'value': 'user3'}
                                    ],
                                )
                            ),
                            html.Div(style={'width':'20px'}),
                            _textWithElementInRow(
                                'End Date Observed',
                                DatePickerSingle(
                                    id='date-picker-single',
                                    # date='2024-09-10',  # Default date
                                    display_format='YYYY-MM-DD',  # Format to display
                                    clearable=True,
                                    reopen_calendar_on_clear=True,
                                )
                            ),
                            html.Div(style={'width':'20px'}),
                            _textWithElementInRow(
                                'Date Range',
                                Input(
                                    id='date-range',
                                    type='number',
                                    placeholder='Enter date range',
                                    value=''  # Default value (empty string)
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
                                                {'label': 'Yes', 'value': 'yes'},
                                                {'label': 'No', 'value': 'no'},
                                                {'label': 'Unsure, need a second opinion', 'value': 'unsure, need a second opinion'}
                                            ],
                                            inline=True,
                                            # style=row_element,
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
                                                    value=0          # Default value
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
                                                {'label': 'Yes', 'value': 'yes'},
                                                {'label': 'No', 'value': 'no'},
                                            ],
                                            inline=True,
                                            labelStyle=text_styling
                                        )
                                    ),
                                    html.Div(
                                        children=[
                                            Input(
                                                id='latitude',
                                                type='text',
                                                placeholder='Latitude',
                                                value=''  # Default value (empty string)
                                            ),
                                            Input(
                                                id='longitude',
                                                type='text',
                                                placeholder='Longitude',
                                                value=''  # Default value (empty string)
                                            ),
                                        ],
                                        style={'margin-left': '10px'}
                                    )
                                ],
                                style={
                                    # 'margin-right': '200px'
                                    'display': 'flex',
                                    'flex-direction': 'column',
                                    'align-content': 'space-around',
                                    'row-gap': '10px'
                                }
                            ),
                            html.Div(style={'width': '10vw'}),
                            html.Div(
                                children=[
                                    html.P('InSAR Phase Anomalies', style=title_text_styling),
                                    Checklist(
                                        id='insar-phase-anomalies',
                                        options=[
                                            {'label': anomaly, 'value': anomaly} for anomaly in insar_phase_anomalies
                                        ],
                                        labelStyle=text_styling
                                    ),
                                    html.Div(
                                        children=[
                                            Checklist(
                                                id='other-checkbox',
                                                options=[{'label': 'Other', 'value': 'Other'}],
                                                labelStyle=text_styling
                                            ),
                                            Input(
                                                id='other-anomaly',
                                                type='text',
                                                placeholder='Enter Anomaly',
                                                style={
                                                    'marginLeft': '10px', 
                                                    'width': '200px', 
                                                    # 'display': 'inline-block'
                                                }
                                            )
                                        ],
                                        style=row_element
                                        # {
                                        #     'display': 'flex',
                                        #     'alignItems': 'center',
                                        #     'marginTop': '10px'
                                        # }
                                    )
                                ],
                                style={
                                    'margin-right': '20vw'
                                }
                            )
                        ],
                        style={**row_element, 'justify-content': 'space-between'}
                    ),
                    html.Div(
                        children=[
                            _textWithElementInRow(
                                'Additional Comments',
                                Input(
                                    id='my-input',
                                    type='text',
                                    placeholder='under 100/200 characters',
                                    value=''  # Default value (empty string)
                                )
                            ),
                            html.Button(
                                'Submit Annotation',
                                id='submit-update-annotation',
                                style=button_style
                            ),
                        ],
                        style={**row_element, 'justify-content': 'space-between', 'align-items': 'flex-end'}
                    )
                ]
            ),
            html.Div(
                style={
                    'width': '30%',
                    'borderLeft': '5px solid black',  # Black border on the left side,
                },
                children=[
                    html.H5('Previous Annotations (End Date: )', style={**title_text_styling, 'margin': '10px 5px'}),
                    html.Div(
                        [
                            _annotationsCard(selected=True),
                            _annotationsCard(),
                            _annotationsCard(),
                            _annotationsCard(),
                            _annotationsCard(),  
                        ],
                        style={'height': '70%', 'overflowY': 'auto'}
                    ),
                    html.Div(
                        [
                            html.Button(
                                'Create New Annotation',
                                id='new-annotation-button',
                                style={
                                    **button_style, 
                                    'margin': '5px 15px', # top and bottom, left and right
                                }
                            ),
                        ], 
                        style={ 'display': 'flex', 'justify-content': 'flex-end' }
                    ),
                ]
            )
        ],
    )