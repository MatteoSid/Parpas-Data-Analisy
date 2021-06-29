# -*- coding: utf-8 -*-
# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px
import pandas as pd
import dash
import csv
import os

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

colors = {
    'background': '#1b1f34',
    'text':       '#7FDBFF'
}

tf = '1H'
data_file = 'TabLogPostTHS'
#data_file = 'TabLogAntTHS'
df = create_df(data_file, timeframe=tf)
#df = df.loc['2020-03-18 7:25:00':'2020-03-21 9:35:00']

fig = px.line(df, width=1800, height=900)

fig.update_layout(
    plot_bgcolor=   colors['background'],
    paper_bgcolor=  colors['background'],
    font_color=     colors['text']
)

app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[

    html.H1(
        children=data_file,
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),

    html.Div(
        children='Grafico delle temperature della tabella ' + data_file + ' con timeframe ' + tf,
        style={
            'textAlign': 'center',
            'color': colors['text']
        }),

    html.Label('Selettore tabella'),
    dcc.Dropdown(
        options=[
            {'label': 'TabLogPostTHS', 'value': 'TabLogPostTHS'},
            {'label': 'TabLogAntTHS', 'value': 'TabLogAntTHS'}
        ],
        value = 'TabLogPostTHS'
    ),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
