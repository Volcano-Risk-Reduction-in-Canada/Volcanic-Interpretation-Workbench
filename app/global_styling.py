
text_styling = {
    'color' : 'black',
    'margin' : '0px 5px'
}
title_text_styling = {**text_styling, 'font-weight': 'bold'}

row_element = {
    'display': 'flex',
    'flexDirection': 'row',
    'alignItems': 'center'
}
# Style dictionary for the button
button_style = {
    'padding': '10px 20px',   # Add padding inside the button
    'backgroundColor': '#007bff',  # Background color of the button
    'color': 'white',         # Text color of the button
    'border': 'none',         # Remove border
    'borderRadius': '5px',    # Rounded corners
    'cursor': 'pointer',      # Pointer cursor on hover
    'fontSize': '16px',       # Font size of the button text
}

# Container style
annotation_card_style = {
    'background-color': 'yellow',
    'border': '2px solid black',
    'padding': '10px',
    'margin': '10px',
    'position': 'relative',  # Ensure container is positioned relatively
    'padding-left': '20px'  # Make space for the triangle
}

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