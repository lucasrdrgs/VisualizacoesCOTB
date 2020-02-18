import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots

dfTri = pd.read_csv('PropGestantePreNatal1trim.csv')
for x in range(2000, 2016): dfTri[str(x)] = dfTri[str(x)].apply(lambda k: k * 100)
dfVac = pd.read_csv('PropGestantesVacina.csv')
for x in range(2000, 2016): dfVac[str(x)] = dfVac[str(x)].apply(lambda k: k * 100)
dfMor = pd.read_csv('RegiaoSaude_TxMortalidadeNeonatal.csv')

CIRS = list(dfTri['CIR'].values)
stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets = stylesheets)

app.layout = html.Div(children = [
	html.H2(children = 'Relação entre imunização de gestantes, pré-natal e mortalidade', style = { 'text-align': 'center' }),
	html.Div(
		id = 'container',
		children = [
			dcc.Graph(
				id = 'graph',
			)
		],
		style = {
			'margin-left': '200px',
		}
	),
	html.Div(
		children = [
			dcc.Slider(
				id = 'ano-slider',
				min = 2000,
				max = 2015,
				marks = {
					i: str(i) for i in range(2000, 2016)
				},
				value = 2000,
				included = False,
			),
		],
		style = {
			'margin': '0 auto',
			'width': '65%',
		}
	)
],
style = {
	'font-family': 'sans-serif',
	'display': 'block',
	'text-align': 'center',
})

@app.callback(Output('graph', 'figure'), [Input('ano-slider', 'value')])
def updateFig(ano):
	if ano is None: return
	MX_MORT = dfMor[str(ano)].max().max()
	MN_MORT = dfMor[str(ano)].min().min()

	MN_X = 100
	for i in dfVac[str(ano)].values:
		if i == 0: continue
		MN_X = min(MN_X, i)
	MN_X -= 5

	rN = len(dfTri)
	sX, sY, sXY, sX2, sY2 = 0, 0, 0, 0, 0

	for i in range(rN):
		tmpX = dfVac.iloc[i]
		tmpY = dfTri.iloc[i]
		sX += tmpX[str(ano)]
		sY += tmpY[str(ano)]
		sX2 += tmpX[str(ano)] ** 2
		sY2 += tmpY[str(ano)] ** 2
		sXY += (tmpX[str(ano)] * tmpY[str(ano)])
		del(tmpX, tmpY)

	rA = float((rN * sXY) - (sX * sY)) / float((rN * sX2) - (sX ** 2)) # float((sY * (sX2)) - (sX * sXY)) / float((rN * sX2) - (sX ** 2))
	rB = (1 / float(rN)) * float(sY - (rA * sX))

	rY = lambda x: rA * x + rB

	fig = {
		'data': [
			go.Scatter(
				x = dfVac[dfVac['CIR'] == str(cir)][str(ano)],
				y = dfTri[dfTri['CIR'] == cir][str(ano)],
				marker = {
					'size': 10,
					'cmax': MX_MORT,
					'cmin': MN_MORT,
					'color': dfMor[dfMor['CIR'] == cir][str(ano)],
					'colorbar': {
						'title': 'Mortalidade neonatal (por mil)',
					} if cir == CIRS[0] else {},
					'colorscale': 'bluered',
				},
				text = 'CIR: ' + str(cir) + '<br>' \
						+ 'Proporção de gestantes vacinadas: ' + dfVac[dfVac['CIR'] == str(cir)][str(ano)].apply(lambda x: '%.2f%%' % x) + '<br>' \
						+ 'Proporção de gestantes que começaram o pré-natal no 1º trimestre de gestação: ' + dfTri[dfTri['CIR'] == cir][str(ano)].apply(lambda x: '%.2f%%' % x) + '<br>' \
						+ 'Mortalidade neonatal: ' + dfMor[dfMor['CIR'] == cir][str(ano)].apply(lambda x: '%.2f por mil' % x),
				hoverinfo = 'text',
				mode = 'markers',
				showlegend = False,
			) for cir in CIRS if dfVac[dfVac['CIR'] == str(cir)][str(ano)].values[0] != 0 and dfTri[dfTri['CIR'] == cir][str(ano)].values[0] != 0
		],
		'layout': go.Layout(
			xaxis = {
				'title': 'Proporção de gestantes vacinadas (%)',
				'range': [-5, 105],
			},
			yaxis = {
				'title': 'Proporção de gestantes que começaram o pré-natal no 1º trimestre de gestação (%)',
				'range': [-5, 105],
			},
			hovermode = 'closest',
			height = 800,
			width = 1500,
			transition = {
				'duration': 600
			},
			shapes = [
				go.layout.Shape(
					type = 'line',
					x0 = MN_X,
					y0 = rY(MN_X),
					x1 = 103,
					y1 = rY(103),
					line = {
						'color': 'LightSeaGreen',
						'width': 5,
					}
				)
			]
		)
	}

	return fig

if __name__ == '__main__':
	app.run_server(debug=True)
	updateFig(2000)
