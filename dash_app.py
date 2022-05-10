import dash
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output
import dash_leaflet as dl
import pandas as pd


app = dash.Dash()

# df = px.data.stocks()
df = pd.read_csv('Data/coherenceMatrix.csv')
fig = px.density_heatmap(df, x="Master", y="Slave", z='Coherence', nbinsx=200, nbinsy=200)

# image_url = "file:///Users/drotheram/GitHub/Volcanic-Interpretation-Workbench/Data/20220411_HH_20220427_HH_adf_wrp_geo.jpg"
# image_url = "http://localhost:8080/geoserver/Volcano-InSAR/wms?service=WMS&version=1.1.0&request=GetMap&layers=Volcano-InSAR%3A20220406_HH_20220414_HH&bbox=-28.0558593351285%2C38.48499959355%2C-27.7549973901825%2C38.72168694795&width=768&height=604&srs=EPSG%3A4326&styles=&format=image%2Fjpeg"
image_url = "http://localhost:8080/geoserver/Volcano-InSAR/wms?service=WMS&version=1.1.0&request=GetMap&layers=Volcano-InSAR%3A20220406_HH_20220414_HH&bbox=-28.0558593351285%2C38.48499959355%2C-27.7549973901825%2C38.72168694795&width=768&height=604&srs=EPSG%3A4326&styles=&format=image%2Fpng"
# image_url = 'http://localhost:8080/geoserver/Volcano-InSAR/wms?service=WMS&version=1.1.0&request=GetMap&layers=Volcano-InSAR%3A20220406_HH_20220414_HH.adf.wrp.geo&bbox=-28.0558593351285%2C38.48499959355%2C-27.7549973901825%2C38.72168694795&width=768&height=604&srs=EPSG%3A4326&styles=&format=application/openlayers'
image_bounds = [[38.48499959355,-28.0558593351285], [38.72168694795, -27.7549973901825]]

app.layout = html.Div(id = 'parent', children = [
    html.H1(id = 'H1', children = 'Volcano InSAR Interpretation Workbench', style = {'textAlign':'center',\
                                            'marginTop':40,'marginBottom':40}),

        # dcc.Dropdown( id = 'dropdown',
        # options = [
        #     {'label':'Garibaldi', 'value':'Garibaldi' },
        #     {'label': 'Meager', 'value':'Meager'},
        #     {'label': 'Cayley =', 'value':'Cayley'},
        #     ],
        # value = 'Garibaldi')

    html.Div(
        dcc.Graph(id = 'graph', figure=fig, style={'width': '500px', 'height': '500px'}),
        style={'width': '49%', 'display': 'inline-block'}),
    # html.Div(
    #     dl.Map([dl.ImageOverlay(opacity=0.5, url=image_url, bounds=image_bounds), dl.TileLayer()], 
    #     bounds=image_bounds,
    #     style={'width': '500px', 'height': '500px'})
    #     ,style={'width': '49%', 'display': 'inline-block'})
    html.Div(
        dl.Map([dl.TileLayer(), 
                dl.WMSTileLayer(url="http://localhost:8080/geoserver/Volcano-InSAR/wms?",
                layers="cite:20220406_HH_20220414_HH.adf.wrp.geo", format="image/png", transparent=True)],
                center=[38, -28], zoom=8,
                style={'width': '500px', 'height': '500px'}),
                style={'width': '49%', 'display': 'inline-block'})
    ])
# @app.callback(
#     Output("graph", "figure"))
#     Input("medals", "value"))
# def filter_heatmap():
#     df = pd.read_csv('Data/coherenceMatrix.csv')
#     # fig = px.imshow(df['Coherence'])
#     fig = px.density_heatmap(df, x="Master", y="Slave", z='Coherence')
#     return fig


if __name__ == '__main__': 
    app.run_server()