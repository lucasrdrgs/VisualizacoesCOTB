import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots

ufs = {
	11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
	21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
	31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP',
	41: 'PR', 42: 'SC', 43: 'RS',
	50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
}

def getChunks(s):
	rev = lambda x: x[::-1]
	chunks = []
	s = rev(str(s))
	for i in range(0, len(s), 3):
		tmp = ''
		for j in range(3):
			if i + j >= len(s): break
			tmp += s[i + j]
		if tmp != '':
			tmp = rev(tmp)
			chunks.append(''.join(tmp))
	return rev(chunks)

def pibStr(pib):
	pib = str(pib * 1000)
	chunks = getChunks(pib)
	suffix = 'thousand'
	if len(pib) >= 13:
		suffix = 'trillion'
	elif len(pib) >= 10:
		suffix = 'billion'
	elif len(pib) >= 7:
		suffix = 'million'
	dec = '.%c' % (chunks[1][0] if len(chunks) >= 2 else 0)
	res = 'R$%s%s %s' % (chunks[0], dec if dec[-1] != '0' else '', suffix)
	return res

topd = pd.read_csv('doencas_en.csv')
idhs = pd.read_csv('idh.csv')
pibs = pd.read_csv('pib.csv')
mort = pd.read_csv('mortes.csv')

stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets = stylesheets)
app.layout = html.Div(children = [
	html.H2(
		children = 'Relations between neonatal mortality, GDP and HDI',
	),
	html.Div(
		id = 'dropdown-wrapper',
		children = [
			html.Label(children = 'Federative Unit selector'),
			html.Br(),
			html.Div(
				children = [
					dcc.Dropdown(
						id = 'dropdown',
						value = 'RO',
						clearable = False,
						placeholder = 'UF',
						style = {
							'width': '100px',
							'text-align': 'center',
						},
						options = [
							{ 'label': ufs[lbl], 'value': ufs[lbl] }
							for lbl in ufs
						]
					)
				],
				style = {
					'display': 'inline-block',
					'padding': '0 10px',
				}
			)
		],
	),
	html.Br(),
	html.Div(
		id = 'slider-wrapper',
		children = [
			dcc.Slider(
				id = 'slider-year',
				min = 2010,
				max = 2015,
				step = 1,
				value = 2010,
				marks = {
					year: {
						'label': str(year),
						'style': { 'color': '#060013' },
					}
					for year in range(2010, 2016)
				},
				included = False,
			),
		],
		style = {
			'width': '40%',
			'margin': '0 auto',
		},
	),
	html.Br(), html.Br(),
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
			'max-width': '80%',
			'min-width': '80%',
		},
	)],
	style = {
		'font-family': 'sans-serif',
		'display': 'block',
		'text-align': 'center',
	},
)

@app.callback(Output('graph', 'figure'), [Input('dropdown', 'value'), Input('slider-year', 'value')])
def updateGraph(drop, year):
	if None in [drop, year]: pass

	totalMortes = topd[(topd['UF'] == drop) & (topd['Ano'] == year)]['Total'].sum()
	ANNOT_TXT = 'Federative Unit: ' + drop + '<br>' + 'Total number of deaths: ' + str(totalMortes) + '<br>' + \
				'GDP: ' + pibs[pibs['Nome'] == drop][str(year)].apply(pibStr).values[0] + '<br>' + \
				'HDI: ' + idhs[idhs['Nome'] == drop][str(year)].apply(lambda x: '%.3f' % x).values[0] + '<br>' + \
				'Neonatal mortality: ' + mort[mort['UF'] == drop][str(year)].apply(lambda x: '%.2f‰' % x).values[0]
	fig = {
		'data': [
			go.Pie(
				labels = topd[(topd['UF'] == drop) & (topd['Ano'] == year)]['CID10'],
				values = topd[(topd['UF'] == drop) & (topd['Ano'] == year)]['Total'],
				hole = 0.6,
				text = None,
				hoverinfo = 'text',
				hovertext = topd[(topd['UF'] == drop) & (topd['Ano'] == year)]['CID10'] + \
							'<br>Deaths: ' + topd[(topd['UF'] == drop) & (topd['Ano'] == year)]['Total'].apply(str) + \
							' (' + topd[(topd['UF'] == drop) & (topd['Ano'] == year)]['Total'].apply(lambda x: '%.1f' % (x * 100 / totalMortes)) + '%)',
			)
		],
		'layout': go.Layout(
			hovermode = 'closest',
			height = 700,
			plot_bgcolor = 'white',
			xaxis = {
				'showticklabels': False,
				'showgrid': False,
				'zeroline': False,
			},
			yaxis = {
				'showticklabels': False,
				'showgrid': False,
				'zeroline': False,
			},
			annotations = [{
				'text': ANNOT_TXT,
				'x': 0.5,
				'y': 0.5,
				'font_size': 18,
				'showarrow': False,
			}],
			legend_orientation = 'v'
		)
	}
	
	return fig

if __name__ == '__main__':
	app.run_server(debug = True)
