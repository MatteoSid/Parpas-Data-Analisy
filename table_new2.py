from dash.dependencies import Input, Output
from data_func import tab_to_df
import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px
import pandas as pd
import shutil
import dash
import os

path = 'table_new/'
path_dest = path + 'csv/'
dataDict = {}

# controllo se la cartella 'csv' è presente. Se c'è la elimino e la ricreo, se non c'è la creo.
if os.path.isdir(path_dest):
    shutil.rmtree(path_dest)
    os.mkdir(path_dest)
else:
    os.mkdir(path_dest)

for filename in os.listdir(path):
    if (filename.endswith('.txt') or filename.endswith('.tab')): 
        df = tab_to_df(path + filename)
        if len(df) > 1:
            dataDict[filename] = df

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    
    #--- TITOLO PAGINA
    html.H1(
    children='TOTALE_SONDE_Rev01',
    style={
        'textAlign': 'center'
        #'color': colors['text']
    }),
    
    #--- TENDINA Timeframe
    dcc.Dropdown(
                id='tf_value',
                options=[
                    {'label': '1 minuto',   'value': '1T'},
                    {'label': '5 minuti',   'value': '5T'},
                    {'label': '15 minuti',  'value': '15T'},
                    {'label': '30 minuti',  'value': '30T'},
                    {'label': '1 ora',      'value': '1H'},
                    {'label': '12 ore',     'value': '12H'},
                    {'label': '1 giorno',   'value': '1D'}],
                value='5T',
                clearable=False
            ),
    
    dcc.Graph(id='graph-with-slider'),
])

@app.callback(
    Output('graph-with-slider', 'figure'),
    Input('tf_value', 'value'))
def update_figure(tf_value):
    filtered_df = df.resample(tf_value).mean()
    fig = px.line(filtered_df, height=900)

    #fig.update_layout(transition_duration=500)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)