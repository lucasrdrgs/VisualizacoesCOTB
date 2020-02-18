import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots

stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', 'https://pastebin.com/raw/gUTNSAa4']

ufs = {
	11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
	21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
	31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP',
	41: 'PR', 42: 'SC', 43: 'RS',
	50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
}

regioes = {
	'North': list(range(11, 18)),
	'Northeast': list(range(21, 30)),
	'Southeast': [31, 32, 33, 35],
	'South': [41, 42, 43],
	'Mid-West': list(range(50, 54))
}

regCores = {
    'North': '#636FFA',
    'Northeast': '#EF553B',
    'Southeast': '#00CC96',
    'South': '#AB63FA',
    'Mid-West': '#FFA15A',
}

def obterRegiao(ufid):
	for reg in regioes:
		if ufid in regioes[reg]:
			return reg

dfMortalidade = pd.read_csv('mortalidade.csv')
dfAgua = pd.read_csv('agua.csv')

df = dfMortalidade.rename(columns={'2000': 'M2000', '2010': 'M2010'})

df['A2000'] = dfAgua['2000']
df['A2010'] = dfAgua['2010']

df['Cod'] = df['UF']
df['UF'] = df['Cod'].apply(lambda x: ufs[x])
df['Região'] = df['Cod'].apply(lambda x: obterRegiao(x))

df = df[['Cod', 'UF', 'Região', 'M2000', 'A2000', 'M2010', 'A2010']]

ACCUM_STEP = 0.15
ACCUM_SKIP = 0.5
ACCUM_INICIO = -((27 * ACCUM_STEP) + (4 * ACCUM_SKIP)) / 2
SPAN_ANOS = 8
MAX_WIDTH = (27 * ACCUM_STEP) + (4 * ACCUM_SKIP) + 2

accum = ACCUM_INICIO
nRegs = [k for k in regioes]
ufCtr = 0
def cumsum(x):
	global accum, nRegs, ufCtr

	k = x + accum

	accum += ACCUM_STEP

	ufCtr += 1
	if ufCtr >= len(regioes[nRegs[0]]):
		ufCtr = 0
		nRegs.pop(0)
		accum += ACCUM_SKIP
	return k

df2000 = df.copy()
df2000['Ano'] = 2000
df2000['PosX'] = df2000['Ano'].apply(lambda x: cumsum(x))
accum = ACCUM_INICIO
nRegs = [k for k in regioes]
ufCtr = 0
df2000.rename(columns={'M2000': 'Mortalidade', 'A2000': 'Abastecimento'}, inplace = True)
df2000 = df2000[['Cod', 'UF', 'Região', 'Ano', 'Mortalidade', 'Abastecimento', 'PosX']]
df2000['Raio'] = df2000['Mortalidade']
df2000['Raio'] = df2000['Raio'].apply(lambda x: 2 * x / df2000['Abastecimento'].apply(lambda y: y / 100))

df2010 = df.copy()
df2010['Ano'] = 2010
df2010['PosX'] = df2010['Ano'].apply(lambda x: cumsum(x))
df2010.rename(columns={'M2010': 'Mortalidade', 'A2010': 'Abastecimento'}, inplace = True)
df2010 = df2010[['Cod', 'UF', 'Região', 'Ano', 'Mortalidade', 'Abastecimento', 'PosX']]
df2010['Raio'] = df2010['Mortalidade']
df2010['Raio'] = df2010['Raio'].apply(lambda x: 2 * x / df2010['Abastecimento'].apply(lambda y: y / 100))

dfs = [df2000, df2010]

del dfMortalidade, dfAgua, df2000, df2010

app = dash.Dash(__name__, external_stylesheets=stylesheets)

app.layout = html.Div(children = [
	html.H2(children = 'Relationship between water supply and neonatal mortality', style = { 'text-align': 'center' }),
	html.Div(children = [
			html.H3(children = ['Select a Federative Unit to highlight:'], style = { 'marginBottom': '0px' }),
			dcc.Dropdown(
		    	id = 'dd-estado',
		    	options = [
		    		{ 'label': 'All federative units', 'value': '*'},
		    	] + [ { 'label': ufs[i], 'value': i } for i in ufs ],
		    	value = '*',
                style = {
                    'width': '20vw',
                    'margin': '0 auto',
                },
                searchable = False,
		    ),
	    ],
	    style = {
	    	'margin': '0 auto',
	    	'width': '60%',
	    	'textAlign': 'center',
	    	'fontFamily': 'sans-serif',
	    }
    ),
    dcc.Graph(
        id = 'relacao-agua',
        figure = { },
    )
], style = {
    'font-family': 'sans-serif',
    'display': 'block',
    'text-align': 'center',
})

@app.callback(
    Output('relacao-agua', 'figure'),
    [Input('dd-estado', 'value')])
def update_output(estado):
    if estado is None: return

    fig = make_subplots(rows = 1, cols = 2, subplot_titles = ['2000', '2010'], horizontal_spacing = 0.025)

    for I in range(2):
        dt = []
        ultimaRegiao = ''
        df = dfs[I]
        for i in df['Cod'].unique():
            scatter = go.Scatter(
                x = df[df['Cod'] == i]['PosX'],
                y = df[df['Cod'] == i]['Abastecimento'],
                mode = 'markers+text',
                textposition = 'top center',
                text = df[df['Cod'] == i]['UF'],
                marker = {
                    'size': df[df['Cod'] == i]['Raio'],
                    'line': { 'color': 'black', 'width': 1 },
                    'color': regCores[obterRegiao(i)],
                },
                name = obterRegiao(i),
                hoverinfo = 'text',
                hovertext = 'Federative Unit: ' + df[df['Cod'] == i]['UF'] + '<br>' + \
                            'Neonatal mortality: ' + df[df['Cod'] == i]['Mortalidade'].apply(lambda x: '%.2f in every 1000' % x) + '<br>' + \
                            'Water supply: ' + df[df['Cod'] == i]['Abastecimento'].apply(lambda x: f'{x}%'),
                showlegend = False,
                # legendgroup = 'legendgroup-1'
            )
            if estado != '*' and estado != i:
                scatter.opacity = 0.25
            obtReg = obterRegiao(i)
            if obtReg != ultimaRegiao and I == 0:
                ultimaRegiao = obtReg
                scatter.legendgroup = 'legendgroup-1'
                scatter.showlegend = True
            fig.add_trace(scatter, row = 1, col = I + 1)

    fig.update_layout(height = 800, hovermode = 'closest', showlegend = True)
    fig.update_layout(
        yaxis = {
            'title': 'Water supply (%)',
            'range': [70, 104],
        },
    )

    fig.update_xaxes(
        tickvals = [2000],
        row = 1, col = 1
    )

    fig.update_xaxes(
        tickvals = [2010],
        row = 1, col = 2
    )

    return fig
if __name__ == '__main__':
    app.run_server(debug=True)
