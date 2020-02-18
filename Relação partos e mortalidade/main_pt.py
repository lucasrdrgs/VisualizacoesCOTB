import time
import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=stylesheets)

siglas_uf = ['RO', 'AC', 'AM', 'RR', 'PA',
			'AP', 'TO', 'MA', 'PI', 'CE',
			'RN', 'PB', 'PE', 'AL', 'SE',
			'BA', 'MG', 'ES', 'RJ', 'SP',
			'PR', 'SC', 'RS', 'MS', 'MT',
			'GO', 'DF']
numeros_uf = [11, 12, 13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 35, 41, 42, 43, 50, 51, 52, 53]
codigos_uf = {numeros_uf[i]: siglas_uf[i] for i in range(0, 27)}
regioes = {
    'Norte': ['AC', 'AM', 'PA', 'RR', 'TO', 'RO', 'AP'],
    'Nordeste': ['MA', 'PI', 'CE', 'RN', 'PE', 'PB', 'SE', 'AL', 'BA'],
    'Centro-Oeste': ['MT', 'MS', 'GO', 'DF'],
    'Sudeste': ['SP', 'RJ', 'MG', 'ES'],
    'Sul': ['PR', 'RS', 'SC']
}

def obterRegiao(r, sigla):
    num = codigos_uf[sigla]
    for key in r:
        if num in r[key]:
            return key
    return None

def scale(x):
    return ((np.log10(2 ** x)) ** 2) + 15

xls = pd.ExcelFile('dados.xlsx')
dfCesarios = pd.read_excel(xls, 0, index_col='UF')
dfHospitalares = pd.read_excel(xls, 1, index_col='Código UF')
dfMortalidade = pd.read_excel(xls, 2, index_col='UF')

dfHospitalares.index.names = ['UF']

rnDict = {
    0: 'Partos cesários (%)',
    1: 'Partos hospitalares (%)',
    2: 'Mortalidade neonatal'
}

# I'm sorry.

dfs = []
# Cada ano, desde 2000 até 2016
for anoI in range(17):
    ano = 2000 + anoI
    dft = pd.DataFrame([dfCesarios[ano], dfHospitalares[ano], dfMortalidade[ano]]).transpose()
    dft.columns = list(rnDict.values()) # ['Partos Cesários (%)', 'Partos Hospitalares (%)', 'Mortalidade (%)']
    dft['Região'] = dft.index
    dft['Região'] = dft['Região'].apply(lambda x: obterRegiao(regioes, x))
    dft['Sigla'] = dft.index
    dft['Sigla'] = dft['Sigla'].apply(lambda x: codigos_uf[x])
    dft['Partos cesários (%)'] = dft['Partos cesários (%)'].apply(lambda x: x * 100)
    dft['Partos hospitalares (%)'] = dft['Partos hospitalares (%)'].apply(lambda x: x * 100)
    dft['Mortalidade neonatal'] = dft['Mortalidade neonatal'].apply(lambda x: float('{0:.1f}'.format(x)))
    dft['Raio'] = dft['Mortalidade neonatal'].apply(scale)
    dft['Ano'] = ano
    dfs.append(dft)

df = pd.concat(dfs)

app.layout = html.Div(children = [
    html.H2(children = 'Relação entre tipos de parto e mortalidade neonatal'),
    dcc.Graph(
        id='relacao-partos',
        figure = {
            'data': []
        }
    ),
    html.Div(id='grafico-slider', style={'width': '60vw', 'margin': '0 auto', 'fontFamily': 'sans-serif', 'textAlign': 'center'}, children=[
        html.Label('Ano:'),
        dcc.Slider(
            id='ano-slider',
            min = 2000,
            max = 2016,
            marks = {
                i: str(i) for i in range(2000, 2017)
            },
            value = 2000,
            included = False,
        ),
        html.Br(), html.Br(),
        html.Label('Delay de transição (ms):'),
        dcc.Slider(
            id='transicao-slider',
            min=0,
            max=1000,
            marks = {
                i: str(i) + ' ms' for i in range(0, 1001, 100)
            },
            value = 500,
            included = False,
        ),
    ]),
],
style = {
    'font-family': 'sans-serif',
    'display': 'block',
    'text-align': 'center',
})

N_CLICKS = 0

@app.callback(Output('relacao-partos', 'figure'),
                [Input('ano-slider', 'value'), Input('transicao-slider', 'value')])
def atualizarFig(slider, transic):
    figura = {
        'data': [
            go.Scatter(
                x = df[(df['Região'] == i) & (df['Ano'] == slider)]['Partos cesários (%)'],
                y = df[(df['Região'] == i) & (df['Ano'] == slider)]['Partos hospitalares (%)'],
                mode = 'markers+text',
                textposition = 'middle right',
                text = df[(df['Região'] == i) & (df['Ano'] == slider)]['Sigla'],
                hovertext = 'UF: ' + df[(df['Região'] == i) & (df['Ano'] == slider)]['Sigla'] + '<br>' + \
                            'Partos cesários: ' + df[(df['Região'] == i) & (df['Ano'] == slider)]['Partos cesários (%)'].apply(lambda x: '%.2f%%' % x) + '<br>' + \
                            'Partos hospitalares: ' + df[(df['Região'] == i) & (df['Ano'] == slider)]['Partos hospitalares (%)'].apply(lambda x: '%.2f%%' % x) + '<br>' + \
                            'Mortalidade neonatal: ' + df[(df['Região'] == i) & (df['Ano'] == slider)]['Mortalidade neonatal'].apply(lambda x: '%.2f%% por mil' % x),
                hoverinfo = 'text',
                marker = {
                    'size': df[(df['Região'] == i) & (df['Ano'] == slider)]['Raio'],
                },
                name = i,
            ) for i in df['Região'].unique()
        ],
        'layout': go.Layout(
            xaxis = {
                'title': 'Partos cesários (%)',
                #'range': [0, 100],
            },
            yaxis = {
                'title': 'Partos hospitalares (%)',
                #'range': [80, 104],
            },
            height = 800,
            hovermode = 'closest',
            transition = {
                'duration': transic,
            },
        )
    }
    return figura

if __name__ == '__main__':
    app.run_server(debug=True)
