from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px
from data_func import *
import pandas as pd
import shutil
import dash
import os

os.system('clear')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# controllo se la cartella 'csv' è presente. Se c'è la elimino e la ricreo, se non c'è la creo.
if os.path.isdir('table/csv'):
    shutil.rmtree('table/csv')
    os.mkdir('table/csv')
else:
    os.mkdir('table/csv')

#per ogni file .txt creo il corrispettivo in .csv nella cartella table/csv
table_list = []
for filename in os.listdir('table/'):
    if filename.endswith(".txt"):
        #t.set_description("Bar desc (file %i)" % i)
        #print(filename[:-4])
        txt_to_csv( filename = 'table/' + filename[:-4],
                    filedest = 'table/csv/' + filename[:-4])
        
        # creo una lista con i nomi delle tabelle da unire
        if not filename[-5:-4].isdigit():
            table_list.append(filename[:-4])

# unisco i csv
for table in table_list:
    create_single_csv('table/', table)

# elimino i file originali e tengo solo i .csv uniti che carico in un dizionario di dataframe
dataDict={}
for filename in os.listdir('table/csv'):
    if not filename.endswith('_all.csv'):
        os.remove('table/csv/'+filename)
    elif filename.endswith('_all.csv'):
        print(filename)
        df = pd.read_csv ('table/csv/'+filename, index_col='DataTime')
        df.index = pd.to_datetime(df.index)
        df = df.resample('5T').mean()
        dataDict[filename[:-4]] = df

app.layout = html.Div([
    
    html.Div([

        #--- TITOLO PAGINA
        html.H1(
        children='Storico temperature',
        style={
            'textAlign': 'center'
            #'color': colors['text']
        }),

        #--- SELETTORE TABELLA
        html.Div(['Tabella:',
            dcc.Dropdown(
                id='tab_name',
                options=[{'label': i, 'value': i} for i in table_list],
                value=table_list[0],
                clearable=False
            )
        ],
        style={ 'width': '48%', 
                'display': 'inline-block'
                }),

        #--- SELETTORE TIMEFRAME
        html.Div(['Timeframe:',
            dcc.Dropdown(
                id='tf_value',
                options=[
                    {'label': '5 minuti',   'value': '5T'},
                    {'label': '15 minuti',  'value': '15T'},
                    {'label': '30 minuti',  'value': '30T'},
                    {'label': '1 ora',      'value': '1H'},
                    {'label': '12 ore',     'value': '12H'},
                    {'label': '1 giorno',   'value': '1D'}],
                value='1H',
                clearable=False
            )
        ],
        style={ 'width': '48%', 
                'float': 'right', 
                'display': 'inline-block'
                })
    ]),

    dcc.Graph(id='indicator-graphic')
])

@app.callback(
    Output('indicator-graphic', 'figure'),
    Input('tab_name', 'value'),
    Input('tf_value', 'value'))
def update_graph(tab_name, tf_value):
    
    df = dataDict[tab_name + '_all']
    if tf_value != '5T':
        df = df.resample(tf_value).mean()
    fig = px.line(df, height=800) #, width=1600, height=700)
    # fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    fig.update_layout(
        #title="Plot Title",
        xaxis_title="Time",
        yaxis_title="Temperature",
        legend_title="Sonde",
        font=dict(
            #family="Courier New, monospace",
            size=16,
            color='black'
            #color="RebeccaPurple"
        )
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=False, port=8051)

