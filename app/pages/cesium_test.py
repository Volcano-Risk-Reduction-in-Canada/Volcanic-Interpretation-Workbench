import dash
import dash_html_components as html
from dash.dependencies import Input, Output

external_css = ['https://cesium.com/downloads/cesiumjs/releases/1.76/Build/Cesium/Widgets/widgets.css']
external_scripts = [{'src':'https://cesium.com/downloads/cesiumjs/releases/1.76/Build/Cesium/Cesium.js'}]

app = dash.Dash(__name__, 
                title='Cesium Test',
                external_scripts=external_scripts,
                external_stylesheets=external_css)

app.layout = html.Div(id='blah',
                      children=[
                          'Testing...',
                          html.Div(id='cesiumContainer')
                      ])

app.clientside_callback(
    '''
    function(id) {
        Cesium.Ion.defaultAccessToken = "any_code_works";
        var viewer = new Cesium.Viewer(id);
        return true;
    }
    ''',
    Output('cesiumContainer', 'data-done'),
    Input('cesiumContainer', 'id')
)

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)