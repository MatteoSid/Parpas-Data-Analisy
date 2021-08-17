from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px
from datetime import date, datetime
from tqdm import tqdm
import pandas as pd
import webbrowser
import threading
import dash
import time
import os
import logging
import sys

logging.basicConfig(format='[%(levelname)s][%(asctime)s]: %(message)s',
                    datefmt='%d-%m-%y %H:%M:%S',
                    filename = ".logfile.log",
                    level=logging.DEBUG
                    )
logging.info('\n------------- Avvio programma')

def tab_to_df(filename):
    
    try:
        file1 = open(filename, "rb")
        df = pd.DataFrame()
    except:
        logging.error('Error: {}. {}, line: {}'.format(sys.exc_info()[0],
                                                sys.exc_info()[1],
                                                sys.exc_info()[2].tb_lineno))
        sys.exit()
    flag_data = 0
    num_file = sum([1 for i in open(filename, "r", errors='ignore')])
    
    pbar = tqdm(file1, desc=filename.split('/')[-1], total=num_file)
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

    # controllo se ci sono colonne nulle e in caso le elimino
    for column in df:
        if (df[column] == 0).all():
            df.drop(column, axis=1, inplace=True)

    df.sort_index(inplace = True)
    return df

def start_webpage():
    address = 8051
    time.sleep(3)
    webbrowser.open('http://127.0.0.1:' + str(address) + '/', new=0)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=False)

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
else:
    logging.debug('Creo i file csv')
    print('\nTrasformo le tabelle per la visualizzazione, potrebbe richiedere qualche minuto...\n')
    try:
        os.mkdir(path_dest)
    except:
        print('Errore: non è stata trovata la cartella "table"')
        logging.error('Error: {}. {}, line: {}'.format(sys.exc_info()[0],
                                                sys.exc_info()[1],
                                                sys.exc_info()[2].tb_lineno))
        sys.exit()
    
    start = time.process_time()
    for filename in os.listdir(path):
        if (filename.endswith('.txt') or filename.endswith('.tab')): 
            df = tab_to_df(path + filename)
            if len(df) > 5:
                df.sort_index(inplace = True)
                dataDict[filename] = df
                df.to_csv(path_dest+filename, index=True)
    logging.debug('File .csv creati in : ' + str(round(((time.process_time() - start)/60), 2)) + ' minuti')

if dataDict != {}:
    logging.debug('Tabelle caricate: ' + str(list(dataDict.keys())))
    t = threading.Thread(target=start_webpage)
    t.start()
else:
    logging.error('Nessuna tabella trovata')
    sys.exit()

app.layout = html.Div([
    
    html.Div([

        #--- TITOLO PAGINA
        html.H1(
        children='Storico temperature (v1.0)',
        style={
            'margin-top': '20px',
            'textAlign': 'center'
            #'color': colors['text']
        }),

        # html.Div(
        #     [
        #         html.H5("Comandi:"),
        #         html.P(
        #             children="\
        #             - trascinare un'area del grafico per visualizzare solo l'area selezionata;\n - doppio click sul grafico per tornare alle dimensioni originali;\n \
        #             - doppio click su una voce nella legenda per visualizzare solo quell'elemento;\n \
        #             - dopio clicl su una voce deselezionata nella legenda per riattivare tutti gli elementi",
        #             #style={"color": "#ffffff"},
        #             className="row"
        #         ),
        #     ],
        #     className="product",
        #     style={ #'width': '20%', 
        #                 'display': 'inline-block',
        #                 "margin-left": "50px",
        #                 "margin-right": "100px"
        #                 }
        # ),

        html.Hr(),

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
                    {'label': '2 ore',      'value': '2H'},
                    {'label': '4 ore',      'value': '4H'},
                    {'label': '6 ore',      'value': '6H'},
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

        #--- CHECKBOX PER L'ATTIVAZIONE DEI MARKERS
        dcc.Checklist(
                id='checklist-item',
                options=[{'label': 'Markers', 'value': 'mk'}],
                #value=[],
                style={ 'width': '20%', 
                        'display': 'inline-block',
                        "margin-left": "50px",
                        "margin-right": "100px",
                        "margin-top":"20px"
                        }),

        html.Hr(),

        #--- INFO TABELLA
        html.Div(
            [
                html.H5("Info Tabella:"),
                html.P(
                    id='test',
                    #style={"color": "#ffffff"},
                    className="row"
                ),
                html.P(
                    id='test2',
                    #style={"color": "#ffffff"},
                    className="row"
                )
            ],
            className="product",
            style={ 'width': '20%', 
                        'display': 'inline-block',
                        "margin-left": "50px",
                        "margin-right": "100px"
                        }
        ),
    ]),

    #--- GRAFICO
    dcc.Graph(id='indicator-graphic')
])

@app.callback(
    Output('indicator-graphic', 'figure'),
    Output('my-date-picker-range', 'min_date_allowed'),
    Output('my-date-picker-range', 'max_date_allowed'),
    Output('my-date-picker-range', 'initial_visible_month'),
    #Output('my-date-picker-range', 'end_date'),
    Output('test', 'children'),
    Output('test2', 'children'),
    Input('tab_name', 'value'),
    Input('tf_value', 'value'),
    Input('output-container-date-picker-range', 'data'),
    Input('checklist-item', 'value'))
def update_graph(tab_name, tf_value, data_range, checklist):
    logging.debug('Tabella selezionata: ' + tab_name)

    df = dataDict[tab_name]
    if tf_value != 'None':
        df = df.resample(tf_value).mean()
        logging.debug('Timeframe cambiato: ' + tf_value)
    
    # mi salvo la data di inizio e quella di fine
    time_start = (str(df.index.min()))[:10]
    time_end = (str(df.index.max()))[:10]

    # se viene selezionato un range di date taglio il dataframe
    if data_range:
        df = df.loc[data_range[0]:data_range[1]]
        logging.debug('Range date cambiato: ' + data_range[0] + '-' + data_range[1])

    fig = px.line(df, height=800) #, width=1600, height=700)

    if checklist == None or checklist == []:
    #--- aggiungo i pallini per vedere quando sono state rilevate le temperature
        fig.update_traces(mode='lines')
        logging.debug('Markers disattivato')
    else:
        fig.update_traces(mode='markers+lines')
        logging.debug('Markers attivato')

    if 'air_cons' in tab_name:
        fig = px.bar(df) #, log_y=True)

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

    
    #datetime.strptime(time_start, '%Y-%m-%d').strftime('%m/%d/%y')
    return fig, time_start, time_end, time_start, \
        'Intervallo tabella: dal ' + datetime.strptime(time_start, '%Y-%m-%d').strftime('%m/%d/%y') \
        + ' al ' + datetime.strptime(time_end, '%Y-%m-%d').strftime('%m/%d/%y'), \
        'Numero punti: ' + str(len(df))

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
    app.run_server(debug=False, port=8051)

