import requests


API_KEY = 'hMx4xoxFotuNFAQkZgOmtrY0ATGIhvto'


def check_errors(response: requests.Response):
    if response.status_code == 400:
        raise requests.HTTPError(f'Обратитесь к разработчику: {response.url} не валиден', response=response)
    elif response.status_code == 401:
        raise requests.HTTPError('Обратитесь к разработчику: Неправильный ключ API', response=response)
    elif response.status_code == 403:
        raise requests.HTTPError(f'Обратитесь к разработчику: Нет доступа к {response.url}', response=response)
    elif response.status_code == 404:
        raise requests.HTTPError(f'Обратитесь к разработчику: {response.url} не найден', response=response)
    elif response.status_code == 500 or response.status_code != 200:
        raise requests.HTTPError(f'Обратитесь к разработчику: Неизвестная ошибка: {response.content}', response=response)


# Получает ключ локации в AccuWeather API по широте и долготе.
def get_location_key_by_lat_lon(lat, lon):
    ret = requests.get('http://dataservice.accuweather.com/locations/v1/cities/geoposition/search', 
                       params={
                           'apikey': API_KEY,
                           'q': f'{lat},{lon}'
                       })
    check_errors(ret)

    return ret.json()['Key']

# Получает ключ локации в AccuWeather API по названию города.
def get_location_key_by_city_name(city_name):
    ret = requests.get('http://dataservice.accuweather.com/locations/v1/cities/search', 
                       params={
                           'apikey': API_KEY,
                           'q': city_name
                       })
    check_errors(ret)
    
    cities = ret.json()
    if len(cities) == 0:
        raise ValueError(f'Не найдено городов с названием {city_name}')
    
    return cities[0]['Key']

# Получает текущую погоду по ключу локации в AccuWeather API.
def get_current_conditions_by_location_key(location_key):
    ret = requests.get(f'http://dataservice.accuweather.com/currentconditions/v1/{location_key}',
                       params={
                            'apikey': API_KEY,
                            'details': 'true'
                       })
    check_errors(ret)

    return ret.json()

# Получает погоду на весь день по ключу локации в AccuWeather API.
def get_1_day_forecast_by_location_key(location_key):
    ret = requests.get(f'http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}',
                       params={
                           'apikey': API_KEY,
                           'details': 'true',
                           'metric': 'true'
                       })
    check_errors(ret)

    return ret.json()

# Получает погоду на 5 дней по ключу локации в AccuWeather API.
def get_5_day_forecast_by_location_key(location_key):
    ret = requests.get(f'http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}',
                       params={
                           'apikey': API_KEY,
                           'details': 'true',
                           'metric': 'true'
                       })
    check_errors(ret)

    return ret.json()

# Получает погоду на 10 дней по ключу локации в AccuWeather API.
def get_10_day_forecast_by_location_key(location_key):
    ret = requests.get(f'http://dataservice.accuweather.com/forecasts/v1/daily/10day/{location_key}',
                       params={
                           'apikey': API_KEY,
                           'details': 'true',
                           'metric': 'true'
                       })
    check_errors(ret)

    return ret.json()

# Получает погоду на 15 дней по ключу локации в AccuWeather API.
def get_15_day_forecast_by_location_key(location_key):
    ret = requests.get(f'http://dataservice.accuweather.com/forecasts/v1/daily/15day/{location_key}',
                       params={
                           'apikey': API_KEY,
                           'details': 'true',
                           'metric': 'true'
                       })
    check_errors(ret)

    return ret.json()
    
# Получает погоду на какое-то количество дней по ключу локации в AccuWeather API.
def get_daily_forecast_by_location_key(location_key, days=1):
    if days <= 1:
        return get_1_day_forecast_by_location_key(location_key)
    if days <= 5:
        return get_5_day_forecast_by_location_key(location_key)
    if days <= 10:
        return get_10_day_forecast_by_location_key(location_key)
    if days <= 15:
        return get_15_day_forecast_by_location_key(location_key)

    raise ValueError(f'Слишком большое количество дней {days}')