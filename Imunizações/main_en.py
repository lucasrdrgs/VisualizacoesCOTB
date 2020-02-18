import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots

FIXO = {
	'x': False,
	'y': False,
}

dfImun = pd.read_csv('imunizacoes.csv')
dfMort = pd.read_csv('mortalidade.csv')
dfCons = pd.read_csv('consultas.csv')

def scale(x):
	return ((np.log10(2 ** x)) ** 2) + 15

ufs = {
	11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
	21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
	31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP',
	41: 'PR', 42: 'SC', 43: 'RS',
	50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
}

nomes = {
	11: 'Rondônia', 12: 'Acre', 13: 'Amazonas', 14: 'Roraima', 15: 'Pará', 16: 'Amapá', 17: 'Tocantins',
	21: 'Maranhão', 22: 'Piauí', 23: 'Ceará', 24: 'Rio Grande do Norte', 25: 'Paraíba', 26: 'Pernambuco', 27: 'Alagoas', 28: 'Sergipe', 29: 'Bahia',
	31: 'Minas Gerais', 32: 'Espirito Santo', 33: 'Rio de Janeiro', 35: 'São Paulo',
	41: 'Paraná', 42: 'Santa Catarina', 43: 'Rio Grande do Sul',
	50: 'Mato Grosso do Sul', 51: 'Mato Grosso', 52: 'Goiás', 53: 'Distrito Federal'
}

stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets = stylesheets)
app.layout = html.Div(children = [
		html.H2(children = 'Relationship between pre-natal appointments, immunizations and neonatal mortality', style = { 'text-align': 'center' }),
		html.Div(
			id = 'graph-wrapper',
			children = [
				dcc.Graph(
					id = 'graph'
				),
			],
			style = {
				'width': '80%',
				'margin': '0 auto',
			},
		),
		html.Div(
			id = 'slider-wrapper',
			children = [
				dcc.Slider(
					id = 'slider-ano',
					min = 2000,
					max = 2016,
					step = 1,
					value = 2000,
					included = False,
					marks = { i: str(i) for i in range(2000, 2017) },
				)
			],
			style = {
				'width': '50%',
				'margin': '0 auto',
			}
		)
	],
	style = {
		'font-family': 'sans-serif',
		'display': 'block',
		'text-align': 'center',
	},
)

regioes = ['Norte', 'Nordeste', 'Sudeste', 'Sul', 'Centro-Oeste']
def obterRegiao(uf):
	index = int(str(uf)[0]) - 1
	return regioes[index]

dfImun['Região'] = dfImun['UF'].apply(obterRegiao)
dfMort['Região'] = dfMort['UF'].apply(obterRegiao)
dfCons['Região'] = dfCons['UF'].apply(obterRegiao)

idsConsultas = [ '_N', '_1_6', '_7_mais' ]

coresRegioes = {
	'Norte': '#636FFA',
	'Nordeste': '#EF553B',
	'Sudeste': '#00CC96',
	'Sul': '#AB63FA',
	'Centro-Oeste': '#FFA15A',
}

tradRegs = {
	'Norte': 'North',
	'Nordeste': 'Northeast',
	'Sudeste': 'Southeast',
	'Sul': 'South',
	'Centro-Oeste': 'Mid-West'
}

JUST_STARTED = True

@app.callback(Output('graph', 'figure'), [
	Input('slider-ano', 'value')
])
def updateGraph(ano):
	global JUST_STARTED
	if ano is None: return

	fig = make_subplots(rows = 1, cols = 3, subplot_titles = ['No appointments', '1 to 6 appointments', '7 or more appointments'], horizontal_spacing = 0.025)

	for j in range(len(idsConsultas)):
		for i in regioes:
			val_x = dfCons[dfCons['Região'] == i][str(ano) + idsConsultas[j]]
			val_y = dfImun[dfImun['Região'] == i][str(ano)]
			mort = dfMort[dfMort['Região'] == i][str(ano)]
			fig.add_trace(
				go.Scatter(
					x = val_x,
					y = val_y,
					mode = 'markers+text',
					textposition = 'middle right',
					text = dfImun[dfImun['Região'] == i]['Sigla'],
					hoverinfo = 'text',
					hovertext = 'Federative Unit: ' + dfImun[dfImun['Região'] == i]['Sigla'] + '<br>' + \
							'Percentage of appointments: ' + val_x.apply(lambda x: '{:.2%}'.format(x / 100.0)) + '<br>' + \
							'Percentage of immunizations: ' + val_y.apply(lambda x: '{:.2%}'.format(x / 100.0)) + '<br>' + \
							'Neonatal mortality: ' + mort.apply(lambda x: f'{x} in every 1000'),
					marker = {
						'size': mort.apply(scale),
						'color': coresRegioes[i],
					},
					name = tradRegs[i],
					showlegend = (j == 0),
				),
				row = 1, col = j + 1,
			)
	
	fig.update_layout(
		yaxis = { 'title': 'Immunizations (%)' },
		height = 700,
		hovermode = 'closest',
	)

	if FIXO['x'] and FIXO['y'] and not JUST_STARTED:
		fig.update_layout(transition = { 'duration': 500 })

	fig.update_xaxes(title_text = 'Coverage of prenatal appointments (%)', row = 1, col = 2)

	for i in range(3):
		fig.update_xaxes(range = [-9, 109] if FIXO['x'] else None, row = 1, col = i + 1)
		fig.update_yaxes(range = [-9, 119] if FIXO['y'] else None, row = 1, col = i + 1)

	JUST_STARTED = False

	return fig

if __name__ == '__main__':
	app.run_server(debug = True)
