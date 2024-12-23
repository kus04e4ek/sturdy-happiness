import requests


def get_from(url, **kwargs):
    try:
        ret = requests.get(url, **kwargs)
    except requests.ConnectionError:
        raise ValueError('Не удалось получить доступ к серверу')
    except requests.Timeout:
        raise ValueError('Слишком долго получал доступ к серверу')
    
    if ret.status_code != 200:
        print(ret.content)
        raise ValueError(f'Возникла ошибка: {ret.json()["error"]}')
    
    return ret
    

def get_data(cities):
    return get_from('http://127.0.0.1:8050/api/get_weather', json={
        'cities': cities
    }).json()
    

def get_graph(url):
    return get_from(url).content
