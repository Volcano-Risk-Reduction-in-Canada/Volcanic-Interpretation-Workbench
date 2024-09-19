#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2024 Government of Canada

Authors:
  - Chloe Lam <chloe.lam@nrcan-rncan.gc.ca>
"""

import dash
from dash import html, callback, dcc
from dash_extensions.enrich import (Output, Input)


# helper components
def gc_line(
    border_width=2,
    line_width=98,
    color='black',
    margin='20px auto 10px'
):
    """
    Creates a horizontal line (HR)
    component with customizable styling.

    This helper function returns a
    horizontal line (`<hr>`) element,
    allowing customization of its width,
    color, and margins. It is typically
    used to visually separate sections
    of a layout.

    Parameters:
    ----------
    border_width : int, optional
        The thickness of the line's border
        in pixels (default is 2).
    line_width : int or float, optional
        The width of the line as a percentage of
        its container's width (default is 98%).
    color : str, optional
        The color of the line's border
        (default is 'black').
    margin : str, optional
        The margin around the line, given as a CSS
        shorthand for top, left-right, and
        bottom (default is '20px auto 10px').

    Returns:
    --------
    html.Hr
        A Dash HTML horizontal rule (HR)
        component with the specified styling.
    """
    # horizontal line
    return html.Hr(
        style={
            'border_width': f'{border_width}px',
            'width': f'{line_width}%',
            'borderColor': color,
            'opacity': 1,
            'borderStyle': 'solid',
            'margin': margin
        }
    )


def gc_header(title):
    """
    Creates a header section with a logo, title,
    and a horizontal line.

    This helper function generates a header containing
    a logo image, a title, and a horizontal line for
    visual separation. It also includes a Dash
    `Location` component to track the current page's URL.

    Parameters:
    ----------
    title : str
        The title text to be displayed in the header.

    Returns:
    --------
    html.Div
        A Dash HTML Div component containing the header elements,
        including a logo, a title, and a horizontal line.
    """
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
                    'height': '30px',
                    'marginLeft': '20px',
                }
            )
        ],
        style={
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
    """
    Callback to navigate to the home page
    when the logo image is clicked.

    This function listens for clicks on the Government of Canada
    logo (with id 'gc-logo-img') and, if clicked,
    redirects the user to the homepage ("/").
    If no click has occurred, the current page remains unchanged.

    Parameters:
    ----------
    n_clicks : int or None
        The number of times the logo image has been clicked.
        Will be `None` if no click has occurred.

    Returns:
    --------
    str or dash.no_update
        Returns the pathname '/' to redirect to the home page if clicked,
        or `dash.no_update` if no click has occurred,
        leaving the page unchanged.
    """
    if n_clicks:
        # Redirect to home page ("/") when the image is clicked
        return '/'
    # Default to the current page if no click has occurred
    return dash.no_update
