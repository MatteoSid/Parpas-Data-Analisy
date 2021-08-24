from dash.dependencies import Input, Output
from datetime import date, datetime

import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px

from tqdm import tqdm
import pandas as pd
import webbrowser
import threading
import logging
import dash
import time
import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QSize
#from PyQt5.QtGui import *


VERSION = '3.0'
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=False)

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

def start_window():
    time.sleep(3)
    app = QApplication(sys.argv)
    web = QWebEngineView()
    web.load(QUrl("http://127.0.0.1:8051"))
    web.show()
    sys.exit(app.exec ())

def start_dash():
    app.run_server(debug=False, port=8051)

def create_data():
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
    
    return dataDict

class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow,self).__init__(*args, **kwargs)

        self.setWindowTitle("Grafici Tabelle")
        self.setMinimumSize(QSize(1700, 900))
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://127.0.0.1:8051/"))
        self.setCentralWidget(self.browser)
        self.show()

dataDict = create_data()

app.layout = html.Div(
    [
    html.Div(
        [
        #--- TITOLO PAGINA
        html.Div(
            [
                html.H1(
                    children='Grafici Tabelle (v{})'.format(VERSION),
                    style={
                        #'height': '3%',
                        'margin-top':       '20px',
                        'textAlign':        'center',
                        'verticalAlign':    'bottom',
                        'margin-bottom':    '10px'}
                    )

                #html.Hr()
            ],
            className='title',
            style={
                'border-width': '10px',
                'border-color': 'black'
            }
        ),

        #--- OPZIONI PAGINA
        html.Div(
            [
            html.Div(
                [
                    'Tabella:',
                    dcc.Dropdown(
                        id='tab_name',
                        className   ='product',
                        options     =[{'label': i, 'value': i} for i in dataDict],
                        value       =next(iter(dataDict)),
                        clearable   =False
                    ),

                    dcc.Checklist(
                            id='checklist-item',
                            options=[{
                                'label': 'Punti',
                                'value': 'mk'
                            }]
                    )
                ],
                className='product',
                style={ 'width':        '15%', 
                        'display':      'inline-block',
                        "margin-left":  "50px",
                        "margin-right": "50px"}
            ),
        
            html.Div(
                [
                    'Timeframe:',
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
                className='product',
                style={ 'width':        '15%', 
                        'display':      'inline-block',
                        "margin-right": "50px",
                        "verticalAlign":"top"}
            ),

            dcc.Store(id='output-container-date-picker-range'),
            
            html.Div(
                [
                    'Intervallo Date',
                    dcc.DatePickerRange(
                        id                          ='my-date-picker-range',
                        clearable                   =True,
                        display_format              ='DD-MM-YYYY',
                        start_date_placeholder_text ='DD-MM-YYYY',
                        number_of_months_shown      =1,
                        day_size                    =50,
                        #end_date                    =date.today(),
                        #with_portal                 =True
                    )
                ],
                className='product',
                style={ 'width':         '18%', 
                        'display':       'inline-block',
                        "verticalAlign": "top"}
            ),

            #--- INFO TABELLA
            html.Div(
                [
                    html.H5("Info Tabella:"),
                    html.P(id='info-range'),
                    html.P(id='info-points')
                ],
                className="info_tab",
                style={ 'width':            '25%',
                        'margin-right':     '30px',
                        'float':            'right', 
                        'display':          'inline-block',
                        "verticalAlign":    "top",
                        'orizontalAlign':   'center'}
            )
            ],
            className='options',
            style={'margin-top': '20px'}
        )
    ]),

    html.Div(
        [
            #--- GRAFICO
            dcc.Graph(
                id='indicator-graphic',
                figure=dict(
                        layout={
                            'plot_bgcolor': "#1A3E4C",
                            'paper_bgcolor' :"#67AFCB"}
                        )
            )
        ],
        style={ 
            "margin-top":    "40px",
            "verticalAlign": "down"},
        className='graph'
    )
])

@app.callback(
    Output('indicator-graphic',     'figure'                ),
    Output('my-date-picker-range',  'min_date_allowed'      ),
    Output('my-date-picker-range',  'max_date_allowed'      ),
    Output('my-date-picker-range',  'initial_visible_month' ),
    Output('my-date-picker-range',  'end_date'              ),
    Output('info-range',            'children'              ),
    Output('info-points',           'children'              ),
    Input('tab_name',               'value'                 ),
    Input('tf_value',               'value'                 ),
    Input('output-container-date-picker-range', 'data'      ),
    Input('checklist-item',          'value'                ))
def update_graph(tab_name, tf_value, data_range, checklist):
    logging.debug('Tabella selezionata: ' + tab_name)

    df = dataDict[tab_name]
    if tf_value != 'None':
        df = df.resample(tf_value).mean()
        logging.debug('Timeframe cambiato: ' + tf_value)
    
    # mi salvo la data di inizio e quella di fine
    time_start  =(str(df.index.min()))[:10]
    time_end    =(str(df.index.max()))[:10]

    # se viene selezionato un range di date taglio il dataframe
    if data_range:
        df = df.loc[data_range[0]:data_range[1]]
        logging.debug('Range date cambiato: ' + data_range[0] + '-' + data_range[1])

    fig = px.line(df, render_mode='webgl', height=800) #, width=1600, height=700)

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
        title           =tab_name,
        xaxis_title     ="Time",
        yaxis_title     ="Value",
        legend_title    ="Sonde",
        font=dict(
            size    =16,
            color   ='black'
            ),
        paper_bgcolor   ="#67AFCB",
        plot_bgcolor    ="#1A3E4C",
        legend = dict(
            bgcolor     ='#1A3E4C'
        ),
        legend_font=dict(
            color       ='#67AFCB'
        )
        )
    
    fig.update_xaxes(showline=False, linewidth=1, linecolor='black', gridcolor='#67AFCB')
    fig.update_yaxes(showline=False, linewidth=1, linecolor='black', gridcolor='#67AFCB')

    return (
        fig, 
        time_start, 
        time_end, 
        time_start, 
        time_end, 
        'Intervallo tabella: dal '+datetime.strptime(time_start, '%Y-%m-%d').strftime('%d/%m/%y') \
        +' al '+datetime.strptime(time_end, '%Y-%m-%d').strftime('%d/%m/%y'),
        'Numero punti: '+str(len(df))
        )

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

    if dataDict != {}:
        t = threading.Thread(target=start_dash)
        # set thread as Daemon così viene ucciso se il thread principale termina
        t.setDaemon(True) 
        t.start()

        time.sleep(3)

        app = QApplication(sys.argv)
        window = MainWindow()

        sys.exit(app.exec())
    else:
        logging.error('Nessuna tabella trovata')
        sys.exit()
