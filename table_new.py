from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px
import pandas as pd
import dash

#column_subset = [   't_HdStUp', 't_HdStLw', 't_DxRiga', 't_DxFond', 't_DxAmb', 't_SxRiga', 
#                    't_SxFond', 't_SxAmb', 't_RigAnt', 't_Amb_Mn', 't_RMnPos', 't_FondMn', 
#                    't_Envir', 'DataTime']

df = pd.read_csv (  'TOTALE_SONDE.csv',
                    #usecols=column_subset,
                    sep=';')
df['DataTime'] = pd.to_datetime(df['DataTime'], format='%d.%m.%Y %H:%M:%S')
df.set_index('DataTime', drop = True, inplace=True)
#df = df.resample('5T').mean()

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
    app.run_server(debug=False, port=8050)