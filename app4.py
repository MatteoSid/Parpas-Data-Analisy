from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px
from data_func import *
import pandas as pd
import shutil
import dash
import os
from datetime import date, datetime
import plotly.graph_objects as go
os.system('clear')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

#--- 1° PARTE: Creazione tabelle e caricamento dati
# se la cartella csv è presente carico i dati in memoria
path = 'table_new2/'
path_dest = path + 'csv/'
dataDict = {}
if os.path.isdir(path_dest):
    for filename in os.listdir(path_dest):
        df = pd.read_csv(path_dest + filename)
        df['DataTime'] = pd.to_datetime(df['DataTime'], format='%Y-%m-%d %H:%M:%S')
        df.set_index('DataTime', drop = True, inplace=True)
        dataDict[filename] = df
    
    for i in dataDict:
        print(i)
else:
    print('Cartella Table/csv/ non trovata.')

app.layout = html.Div([
    
    html.Div([

        #--- TITOLO PAGINA
        html.H1(
        children='Storico temperature (v1.0)',
        style={
            'textAlign': 'center'
            #'color': colors['text']
        }),

        #--- SELETTORE TABELLA
        html.Div(['Tabella:',
            dcc.Dropdown(
                id='tab_name',
                options=[{'label': i, 'value': i} for i in dataDict],
                value=next(iter(dataDict)),
                clearable=False
            )
        ],
        style={ 'width': '20%', 
                'display': 'inline-block',
                "margin-left": "50px",
                "margin-right": "100px"
                }),

        #--- SELETTORE TIMEFRAME
        html.Div(['Timeframe:',
            dcc.Dropdown(
                id='tf_value',
                options=[
                    {'label': 'Dati grezzi', 'value': 'None'},
                    {'label': '30 minuti',  'value': '30T'},
                    {'label': '1 ora',      'value': '1H'},
                    {'label': '12 ore',     'value': '12H'},
                    {'label': '1 giorno',   'value': '1D'}],
                value='None',
                clearable=False
            )
        ],
        style={ 'width': '20%', 
                #'float': 'right', 
                'display': 'inline-block',
                "margin-right": "100px"
                }),

        # html.Div(['Intervallo Date (non funziona)',
        #     dcc.DatePickerRange(
        #         id='my-date-picker-range',
        #         min_date_allowed=date(2019, 1, 1),
        #         max_date_allowed=date.today(),
        #         initial_visible_month=date(2019, 1, 1),
        #         end_date=date.today(),
        #         display_format='DD-MM-YYYY',
        #         start_date_placeholder_text='DD-MM-YYYY'

        #     )
        # ],
        # style={ 'width': '20%', 
        #         'float': 'right', 
        #         'display': 'inline-block'
        #         }),
    
        html.Hr()

    ]),

    dcc.Graph(id='indicator-graphic')
])

@app.callback(
    Output('indicator-graphic', 'figure'),
    Input('tab_name', 'value'),
    Input('tf_value', 'value'))
def update_graph(tab_name, tf_value):
    if tf_value != 'None':
        df = dataDict[tab_name]
        df = df.resample(tf_value).mean()
    else:
        df = dataDict[tab_name]

    fig = px.line(df, height=800) #, width=1600, height=700)

    #--- aggiungo i pallini per vedere quando sono state rilevate le temperature
    #fig.update_traces(mode='markers+lines')

    # fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    fig.update_layout(
        #title="Plot Title",
        xaxis_title="Time",
        yaxis_title="Value",
        legend_title="Sonde",
        font=dict(
            #family="Courier New, monospace",
            size=16,
            color='black'
            #color="RebeccaPurple"
            ))

    return fig

if __name__ == '__main__':
    app.run_server(debug=False, port=8051)

