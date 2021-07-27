from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px
from datetime import date
from tqdm import tqdm
import pandas as pd
import webbrowser
import threading
import dash
import time
import os

def tab_to_df(filename):
        
    file1 = open(filename, "rb")
    df = pd.DataFrame()
    flag_data = 0
    num_file = sum([1 for i in open(filename, "r", errors='ignore')])
    
    pbar = tqdm(file1, desc=filename, total=num_file)
    for line in pbar:

        if b'\xb0C' in line:     # se trovo il carattere °C lo ignoro
            pass
        else:
            line = line.decode() # altrimenti decodifico la riga

            # cerco la riga con i nomi della tabella
            if line.startswith('NR'):
                flag_data = 1                  # quando trovo i nomi delle colonne imposto flag_data = 1
                table_names = line.split()     # divido i nomi delle colonne      
                table_names.remove('LastLine') # elimino 'LastLine' che fa riferimento ad un singolo dato duplicato
                
                # definisco i nomi delle colonne del dataframe
                df = df.reindex(columns = table_names)

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
                    
                    df_length = len(df)
                    df.loc[df_length] = row
    
    #df['DataTime'] = pd.to_datetime(df['DataTime'], format='%H:%M:%S %d.%m.%y', errors='coerce')
    df.set_index('DataTime', drop = True, inplace=True)
    df.index = pd.to_datetime(df.index, format='%H:%M:%S %d.%m.%Y')
    df.drop('NR', axis=1, inplace=True)
    
    for column in df.keys():
        if 'PLC_' in column or column == 'OpMode':
            df.drop(column, axis=1, inplace=True)
        else:
            df[column] = df[column].apply(pd.to_numeric)
    return df

def start_webpage():
    address = 8051
    time.sleep(3)
    webbrowser.open('http://127.0.0.1:' + str(address) + '/', new=0)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

#--- 1° PARTE: Creazione tabelle e caricamento dati
# se la cartella csv è presente carico i dati in memoria
path = os.getcwd() + '/table/'
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
    print('\nTrasformo le tabelle per la visualizzazione, potrebbe richiedere qualche minuto...\n')
    os.mkdir(path_dest)
    for filename in os.listdir(path):
        if (filename.endswith('.txt') or filename.endswith('.tab')): 
            df = tab_to_df(path + filename)
            if len(df) > 5:
                #df = df.resample('10T').mean()
                df.sort_index(inplace = True)
                dataDict[filename] = df
                df.to_csv(path_dest+filename, index=True)

    for i in dataDict:
        print(i)

t = threading.Thread(target=start_webpage)
t.start()

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

        #--- CHECKBOX
        # html.Div(['prova',
        #     dcc.Checklist(
        #         id='checklist-item',
        #         options=[{'label': 'Markers', 'value': 'mk'}]
        #         )],
        # style={ #'width': '20%', 
        #         #'float': 'left', 
        #         'display': 'inline-block'
        #         }),

        #--- INTERVALLO DATE
        dcc.Store(id='output-container-date-picker-range'),
        html.Div(['Intervallo Date',
            dcc.DatePickerRange(
                id='my-date-picker-range',
                #min_date_allowed=date(2021, 1, 1),
                clearable=True,
                #max_date_allowed=date.today(),
                #initial_visible_month=date(2021, 1, 1),
                end_date=date.today(),
                display_format='DD-MM-YYYY',
                start_date_placeholder_text='DD-MM-YYYY'
            )
        ],
        style={ 'width': '20%', 
                'float': 'right', 
                'display': 'inline-block'
                }),

        html.Hr(),

        dcc.Checklist(
                id='checklist-item',
                options=[{'label': 'Markers', 'value': 'mk'}],
                #value=[],
                style={ 'width': '20%', 
                        'display': 'inline-block',
                        "margin-left": "50px",
                        "margin-right": "100px"
                        })

    ]),
    dcc.Graph(id='indicator-graphic')
])

@app.callback(
    Output('indicator-graphic', 'figure'),
    Output('my-date-picker-range', 'min_date_allowed'),
    Output('my-date-picker-range', 'max_date_allowed'),
    Output('my-date-picker-range', 'initial_visible_month'),
    #Output('my-date-picker-range', 'end_date'),
    Input('tab_name', 'value'),
    Input('tf_value', 'value'),
    Input('output-container-date-picker-range', 'data'),
    Input('checklist-item', 'value'))
def update_graph(tab_name, tf_value, data_range, checklist):

    if tf_value != 'None':
        df = dataDict[tab_name]
        df = df.resample(tf_value).mean()
    else:
        df = dataDict[tab_name]
    
    if data_range:
        df = df.loc[data_range[0]:data_range[1]]

    fig = px.line(df, height=800) #, width=1600, height=700)

    if checklist == None or checklist == []:
    #--- aggiungo i pallini per vedere quando sono state rilevate le temperature
        fig.update_traces(mode='lines')
    else:
        fig.update_traces(mode='markers+lines')

    fig.update_layout(
        #title=prova,
        xaxis_title="Time",
        yaxis_title="Value",
        legend_title="Sonde",
        font=dict(
            #family="Courier New, monospace",
            size=16,
            color='black'
            #color="RebeccaPurple"
            ))

    time_start = (str(dataDict['Long_term_temp.tab'].index.min()))[:10]
    time_end = (str(dataDict['Long_term_temp.tab'].index.max()))[:10]

    return fig, time_start, time_end, time_start

@app.callback(
    dash.dependencies.Output('output-container-date-picker-range', 'data'),
    [dash.dependencies.Input('my-date-picker-range', 'start_date'),
     dash.dependencies.Input('my-date-picker-range', 'end_date')])
def update_output(start_date, end_date):
    if start_date is not None:
        start_date_object = date.fromisoformat(start_date)
    if end_date is not None:
        end_date_object = date.fromisoformat(end_date)
    if start_date == None or end_date == None:
        return False
    else:
        return [start_date_object, end_date_object]

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)

