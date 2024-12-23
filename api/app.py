import requests
import pathlib

import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

from datetime import datetime

from dash import Dash, dcc, html, Input, Output, State
from flask import request, jsonify, send_file

from city_weather import CityWeather


app = Dash(__name__, suppress_callback_exceptions=True)
app.title = 'Погода'

app.layout = html.Div([
    html.Div(id='error'),
    html.Div([
        html.Div([
            html.Div([
                html.Label('Начальная точка:'),
                dbc.Input(type='text', value=''),
                html.Br(),
                html.Br(),
            ]),
            html.Div([
                html.Label('Конечная точка:'),
                dbc.Input(type='text', value=''),
                html.Br(),
                html.Br(),
            ]),
        ], id='cities'),
        html.Button('Добавить город', id='add-city', n_clicks=0),
        html.Button('Удалить город', id='delete-city', n_clicks=0),
        html.Button('Получить погоду', id='submit', n_clicks=0),
    ]),
    html.Div(id='response'),
])


@app.callback(
    Output('cities', 'children', True),
    Input('add-city', 'n_clicks'),
    State('cities', 'children'),
    prevent_initial_call = True
)
def add_city(n_clicks, children):
    if n_clicks == 0:
        return children
    
    return children[0:-1] + [
            html.Div([
                html.Label(f'Промежуточная точка {len(children) - 1}:'),
                dbc.Input(type='text', value=''),
                html.Br(),
                html.Br(),
            ]),
            children[-1]
        ]


@app.callback(
    Output('cities', 'children', True),
    Input('delete-city', 'n_clicks'),
    State('cities', 'children'),
    prevent_initial_call = True
)
def delete_city(n_clicks, children):
    if n_clicks == 0 or len(children) <= 2:
        return children
    
    return children[0:-2] + [children[-1]]


@app.callback(
    Output('response', 'children'),
    Output('error', 'children'),
    Input('submit', 'n_clicks'),
    State('cities', 'children'),
    State('response', 'children')
)
def get_cities(n_clicks, cities_children, response_children):
    if n_clicks == 0:
        return response_children, None
    
    city_names = [(i['props']['children'][0]['props']['children'], i['props']['children'][1]['props']['value']) for i in cities_children]
    if not all(i[1] for i in city_names):
        return response_children, [
            html.H1('Не введено название городов')
        ]
    
    try:
        city_weathers = [CityWeather.get_by_city_name(i[1], 5) for i in city_names]
    except requests.ConnectionError:
        return response_children, [
            html.H1('Не удалось получить доступ к AccuWeather')
        ]
    except requests.Timeout:
        return response_children, [
            html.H1('Слишком долго получал доступ AccuWeather')
        ]
    except Exception as exception:
        return response_children, [
            html.H1(str(exception))
        ]
    
    return [
        dcc.Store('city-weathers', data=[i.to_dict() for i in city_weathers]),
        html.Div([
            dcc.Dropdown([
                {'label': 'Без графика', 'value': 'Без графика'},
                {'label': 'Температура', 'value': 'Температура'},
                {'label': 'Влажность', 'value': 'Влажность'},
                {'label': 'Скорость ветра', 'value': 'Скорость ветра'},
                {'label': 'Вероятность дождя', 'value': 'Вероятность дождя'},
            ], value='Без графика', id='graph-type'),
            dcc.Dropdown([
                {'label': '3', 'value': '3'},
                {'label': '5', 'value': '5'},
            ], value='5', id='number-of-days'),
            dcc.Graph('graph-cities'),
        ]),
        html.Div([
            html.Div([
                html.H1(f'{city_names[idx][0]} {i.city_name}'),
                html.P(f'Температура: {i.current.temperature}'),
                html.P(f'Влажность: {i.current.humidity}'),
                html.P(f'Скорость ветра: {i.current.wind_speed}'),
                html.P(f'Вероятность дождя: {i.current.rain_probability}')
            ])
            for idx, i in enumerate(city_weathers)
        ]),
        html.H1(
            'Погода плохая' if any(i.check_bad_weather() for i in city_weathers)
            else 'Погода хорошая'
        )
    ], None


def get_dataframe_from_city_weathers(city_weathers, number_of_days):
    days = ['Сегодня', 'Завтра', 'Послезавтра', 'Через 3 дня', 'Через 4 дня'] + [
        f'Через {i} дней' for i in range(5, 16)
    ]
    return pd.DataFrame([
        [i.city_name, j.temperature, j.humidity, j.wind_speed, j.rain_probability, days[idx]]
        for i in city_weathers for idx, j in enumerate(i.forecast[:int(number_of_days)])
    ], columns=['city', 'temperature', 'humidity', 'wind_speed', 'rain_probability', 'day'])

def get_graph(dataframe, graph_type):
    graph_type = graph_type.replace('_', ' ')
    
    if graph_type == 'Температура':
        return px.line(dataframe, x='day', y='temperature', color='city').update_layout(xaxis_title='День', yaxis_title='Температура')
    if graph_type == 'Влажность':
        return px.line(dataframe, x='day', y='humidity', color='city').update_layout(xaxis_title='День', yaxis_title='Влажность')
    if graph_type == 'Скорость ветра':
        return px.line(dataframe, x='day', y='wind_speed', color='city').update_layout(xaxis_title='День', yaxis_title='Скорость ветра')
    if graph_type == 'Вероятность дождя':
        return px.line(dataframe, x='day', y='rain_probability', color='city').update_layout(xaxis_title='День', yaxis_title='Вероятность дождя')
    
    return px.line()


@app.callback(
    Output('graph-cities', 'figure', True),
    Input('graph-type', 'value'),
    Input('number-of-days', 'value'),
    State('city-weathers', 'data'),
    prevent_initial_call = True
)
def change_graph_type(graph_type, number_of_days, city_weathers_dict):
    city_weathers = [CityWeather(**i) for i in city_weathers_dict]
    
    df = get_dataframe_from_city_weathers(city_weathers, number_of_days)
    return get_graph(df, graph_type)


@app.server.route('/api/get_weather', methods=['GET'])
def get_weather():
    data = request.get_json(True, True)
    if data is None:
        return jsonify({'error': 'Некорректный json'}), 400
    
    if 'cities' not in data:
        return jsonify({'error': 'Поле "cities" не найдено в json'}), 400
    
    try:
        city_weathers = [CityWeather.get_by_city_name(i, 5) for i in data['cities']]
    except requests.ConnectionError:
        return jsonify({'error': 'Не удалось получить доступ к AccuWeather'}), 503
    except requests.Timeout:
        return jsonify({'error': 'Слишком долго получал доступ AccuWeather'}), 504
    except Exception as exception:
        return jsonify({'error': str(exception)}), 520
    
    df_3 = get_dataframe_from_city_weathers(city_weathers, 3)
    df_5 = get_dataframe_from_city_weathers(city_weathers, 5)
    
    parent = pathlib.Path(__file__).parent.resolve()
    pathlib.Path(f'{parent}/static/graphs/').mkdir(parents=True, exist_ok=True)
    
    id = datetime.now().isoformat()
    for i in ('Температура', 'Влажность', 'Скорость_ветра', 'Вероятность_дождя'):
        get_graph(df_3, i).write_image(file=f'{parent}/static/graphs/{id}_{i}_3.jpg')
        get_graph(df_5, i).write_image(file=f'{parent}/static/graphs/{id}_{i}_5.jpg')
    
    return jsonify({
        'cities': [i.to_dict() for i in city_weathers],
        'graphs': {
            i: {
                '3': f'{request.url_root}api/graph?id={id}&type={i}&days=3',
                '5': f'{request.url_root}api/graph?id={id}&type={i}&days=5'
            }
            for i in ('Температура', 'Влажность', 'Скорость_ветра', 'Вероятность_дождя')
        }
    })


@app.server.route('/api/graph', methods=['GET'])
def get_graph_image():
    if 'id' not in request.args:
        return jsonify({'error': 'Поле "id" не найдено в аргументах'}), 400
    if 'type' not in request.args:
        return jsonify({'error': 'Поле "type" не найдено в аргументах'}), 400
    if 'days' not in request.args:
        return jsonify({'error': 'Поле "days" не найдено в аргументах'}), 400
    
    id = request.args['id']
    type = request.args['type']
    days = request.args['days']
    
    parent = pathlib.Path(__file__).parent.resolve()
    if not pathlib.Path(f'{parent}/static/graphs/{id}_{type}_{days}.jpg').exists():
        return jsonify({'error': 'Не найден график'}), 404
    
    return send_file(f'{parent}/static/graphs/{id}_{type}_{days}.jpg', 'image/jpeg')


if __name__ == '__main__':
    app.run(debug=True)
