from _plotly_utils.basevalidators import AnyValidator
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import os, csv

import pandas as pd

def txt_to_csv(filename, filedest):

    if os.path.isfile(filedest + '.csv'):
        os.remove(filedest + '.csv')

    file = open(filename + '.txt', "rb")
    file_csv = open(filedest + '.csv', 'w+', newline ='')

    count = 0
    flag_data = 0
    with file_csv:
        for line in file:
            if b'\xb0C' in line:     # se trovo il carattere °C lo ignoro
                pass
            else:
                line = line.decode() # altrimenti decodifico la riga
                # cerco la riga con i nomi della tabella
                if line.startswith('NR'):
                    flag_data = 1                  # quando trovo i nomi delle colonne imposto flag_data = 1
                    table_names = line.split()     # divido i nomi delle colonne
                    table_names.remove('LastLine') # elimino 'LastLine' che fa riferimento ad un singolo dato duplicato
                    #for item in table_names: print(item)
                    write = csv.writer(file_csv)
                    write.writerow(table_names)
                # Se sono arrivato alla tabella ma la riga inizia con 0 la salto
                elif flag_data == 1 and line.startswith('0'):
                    pass
                # Se sono arrivato alla tabella (flag_data == 1) e non sono alla prima riga
                # inizio a salvare i dati
                elif flag_data == 1:
                    row = line.split()

                    if not line.startswith('[END]') and len(row) == len(table_names)+1: # le righe con meno di 25 elementi hanno dati mancanti
                        row[-2] = str(row[-2]) + ' ' + str(row[-1]) # unisco l'ora col giorno
                        del row[-1] # elimino la colonna con i giorni
                        write = csv.writer(file_csv)
                        write.writerow(row)
                        count = count+1      # aggiorno il contatore delle righe

def load_data(file):

    df = pd.read_csv (file, index_col=False)
    df['DataTime'] = pd.to_datetime(df['DataTime'], format='%H:%M:%S %d.%m.%Y')
    df.set_index('DataTime', drop = True, inplace=True)
    if not df.index.is_monotonic: df.sort_index(inplace = True)
    df.drop('NR', axis=1, inplace=True)
    return df

def create_df(file, timeframe='1H'):
    path = 'Tabelle_omv/'
    data_list=[]

    for filename in os.listdir(path):
        if filename.endswith(".txt") and file in filename:
            print(filename[:-4])
            txt_to_csv(filename = path + filename[:-4],
                        filedest = path + 'csv/' + filename[:-4])

            data = load_data(path + 'csv/' + filename[:-4] + '.csv')
            data_list.append(data)

    data_all = pd.concat(data_list)
    data_all.sort_index(inplace = True)

    data_all = data_all.resample(timeframe).mean()
    return data_all

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


available_tab = ['TabLogPostTHS', 'TabLogAntTHS', 'DiagnosisTabl', 'DiagnosisTable', 'TabLogFMS_DX', 'TabLogFMS_SX']
available_tf = ['10T', '30T', '1H', '12H', '1D']

'''
app.layout = html.Div([
    html.H6("Change the value in the text box to see callbacks in action!"),
    html.Div(["Input: ",
                dcc.Input(id='my-input', value='initial value', type='text')]),
    html.Br(),
    html.Div(id='my-output'),

])
'''

app.layout = html.Div([
    html.Div([

        html.H1(
        children='Storico temperature',
        style={
            'textAlign': 'center'
            #'color': colors['text']
        }),

        html.Div(['Tabella:',
            dcc.Dropdown(
                id='tab_name',
                options=[{'label': i, 'value': i} for i in available_tab],
                value='TabLogPostTHS'
            )
        ],
        style={'width': '48%', 'display': 'inline-block'}),

        html.Div(['Timeframe:',
            dcc.Dropdown(
                id='tf_value',
                options=[
                    {'label': '30 minuti', 'value': '30T'},
                    {'label': '1 ora', 'value': '1H'},
                    {'label': '12 ore', 'value': '12H'},
                    {'label': '1 giorno', 'value': '1D'}
                ],
                value='1H'
            )
        ],style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ]),

    dcc.Graph(id='indicator-graphic')

])

@app.callback(
    Output('indicator-graphic', 'figure'),
    Input('tab_name', 'value'),
    Input('tf_value', 'value'))
def update_graph(tab_name, tf_value):

    df2 = create_df(tab_name, timeframe=tf_value)
    fig = px.line(df2, height=700) #, width=1600, height=700)
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
    app.run_server(debug=True, port=8051)