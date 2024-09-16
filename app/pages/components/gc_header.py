import dash
from dash import html, callback, dcc
from dash_extensions.enrich import (Output, Input)

# helper components
def gc_line(borderWidth=2, lineWidth=98, color='black', margin='20px auto 10px'):
    # horizontal line
    return html.Hr(
        style={
            'borderWidth': f'{borderWidth}px',
            'width': f'{lineWidth}%',
            'borderColor': color,
            'opacity': 1,
            'borderStyle': 'solid',
            'margin': margin
        }
    )


def gc_header(title):
    return html.Div(
        children=[
             # This component will track the current page's URL
            dcc.Location(id='url', refresh=True),
            html.Img(
                src='assets/GOVCan_FIP_En.png',
                style={
                    'height': '30px',
                    'position': 'relative',
                    'left': '15px',
                    'top': '10px'
                },
                id='gc-logo-img'
            ),
            gc_line(),
            html.H5(
                id='Title',
                children=title,
                style={
                    'color': 'black',
                    # 'background-color': 'white',
                    # 'text-align': 'center',
                    'height': '30px',
                    'marginLeft': '20px',
                }
            ),
        ],
        style={
            # 'display': 'flex',
            # 'flex-direction': 'column',
            'background-color': 'white',
            'height': '100px',
            'width': '100%',
        }
    )

# Callback to handle page routing
@callback(
    Output('url', 'pathname'),
    Input('gc-logo-img', 'n_clicks')
)
def navigate_to_home(n_clicks):
    if n_clicks:
        # Redirect to home page ("/") when the image is clicked
        return '/'
    # Default to the current page if no click has occurred
    return dash.no_update