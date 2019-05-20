import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from dash.dependencies import Input, Output, State

import pandas as pd
import plotly.graph_objs as go

from dateutil.relativedelta import relativedelta
import datetime

df = pd.read_csv('data_sample.csv', parse_dates=['ts'])
#TODO:
# Combine specific columns into same graph
# liquid_rate_in_hr,ice_rate_in_hr,snow_rate_in_hr
# horizontal_mf_salt
# road_liq_depth_in,road_ice_depth_in,road_unbndice_depth_in,road_cmpsnw_in,road_snow_depth_in
# prct_ice,
# speed_mph,profile_speed,
# ref_speed
# imputed
# rel_speed
# 3 groups observed from the data.
# group1 = [0, 1, 2]
# group2 = [4, 5, 6, 7, 8]
# group3 = [10, 11, 14]

epoch = datetime.datetime.utcfromtimestamp(0)


def unix_time_millis(dt):
    return int((dt - epoch).total_seconds())


def get_marks_from_start_end(start, end):
    result = []
    current = start
    while current <= end:
        result.append(current)
        current += relativedelta(months=1)
    return {unix_time_millis(m): {'label':str(m.strftime('%Y-%m'))} for m in result}


def get_points_from_dataframe(date_millis, value):
    points = []
    for i in range(24):
        time = datetime.datetime.utcfromtimestamp(date_millis + 3600 * i)
        filtered_df = df[df.ts == time]
        if len(filtered_df) > 0:
            points.append(float(filtered_df[value]))
        else:
            break
    return points


external_stylesheets = None
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    daq.ToggleSwitch(
        id='color-toggle',
        label='Color',
        labelPosition='bottom'
    ),
    dcc.Dropdown(id='options',
                 options=[{'label': s, 'value': s} for s in df.columns[1:]],
                 value=[df.columns[1]],
                 multi=True),
    html.Div(
        dcc.Slider(
            id='date-slider',
            updatemode='mouseup',
            min=unix_time_millis(df['ts'].min()),
            max=unix_time_millis(df['ts'].max()),
            value=unix_time_millis(df['ts'].min()),
            step=86400,  # length of each day
            marks=get_marks_from_start_end(df['ts'].min(), df['ts'].max())
        ),
        style={'margin': '1em'}),
    html.Div(id='date-selection'),
    html.Div(children=html.Div(id='graphs'))

],
    id='layout',
    style={'margin': '1em'}
)


@app.callback(
    [Output('color-toggle', 'label'),
     Output('layout', 'style')],
    [Input('color-toggle', 'value')]
    )
def update_toggle(value):
    return ['Black', {'filter': 'grayscale(100%)'}] if value else ['Color', {}]


@app.callback(
    Output('graphs', 'children'),
    [Input('options', 'value'),
     Input('date-slider', 'value')]
    )
def update_graphs(selections, selected_date):
    graphs = []
    for i, selection in enumerate(selections):
        points = get_points_from_dataframe(int(selected_date), selection)
        data = [go.Scatter(
            x=list(range(len(points))),
            y=points,
            mode='lines+markers',
            opacity=0.7,
            # TODO:
            #  add more information in marker label
            marker={
                'size': 10,
                'color': 'blue',
                'line': {'width': 0.5}
            }
        )]

        graphs.append(html.Div(dcc.Graph(
            id=selection,
            figure={'data': data,
                    'layout': go.Layout(
                        xaxis={'title': 'Hour'},
                        margin={'l': 100, 'b': 40, 't': 40, 'r': 100},
                        title=f"{selection}",
                        legend={'x': 0, 'y': 1},
                        hovermode='closest'
                    )
                    }
            )))

    return graphs


@app.callback(
    Output('date-selection', 'children'),
    [Input('date-slider', 'value')]
    )
def update_selected_date(selected_date):
    return f"Date: {str(datetime.datetime.utcfromtimestamp(int(selected_date)).strftime('%Y-%m-%d'))}"


if __name__ == '__main__':
    app.run_server()
