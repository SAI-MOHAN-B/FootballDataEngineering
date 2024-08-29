# https://en.wikipedia.org/wiki/List_of_association_football_stadiums_by_capacity
import pandas as pd
import json
from geopy.geocoders import Nominatim
from datetime import datetime

NO_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/No-image-available.png/480px-No-image-available.png'


def get_wikipedia_page(url):
    import requests
    print("Getting Wikipedia Page.....", url)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # check if the request is successfully

        return response.text
    except requests.RequestException as e:
        print(f' An Error Occured:{e}')


def get_wikipedia_data(html):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find_all("table", {"class": "wikitable"})[1]
    table_rows = table.find_all('tr')
    return table_rows


def clean_text(text):
    text = str(text).strip()
    text = text.replace('&nbsp', '')
    if text.find('♦'):
        text = text.split('♦')[0]
    if text.find('[') != -1:
        text = text.split('[')[0]
    if text.find('(formerly)') != -1:
        text = text.split('(formerly)')[0]
    if text == '\n':
        return ""
    return text.replace('\n', '')


def extract_wikipedia_data(**kwargs):
    import json
    url = kwargs['url']
    html = get_wikipedia_page(url)
    rows = get_wikipedia_data(html)

    data = []

    for i in range(1, len(rows)):
        tds = rows[i].find_all('td')
        values = {
            'rank': i,
            'stadium': clean_text(tds[0].text),
            'capacity': clean_text(tds[1].text).replace(',', '').replace('.', ''),
            'region': clean_text(tds[2].text),
            'country': clean_text(tds[3].text),
            'city': clean_text(tds[4].text),
            'images': 'https://' + tds[5].find('img').get('src').split("//")[1] if tds[5].find('img') else " NO_IMAGE",
            'home_team': clean_text(tds[6].text)

        }
        data.append(values)
    json_rows = json.dumps(data)
    kwargs['ti'].xcom_push(key='rows', value=json_rows)
    return "ok"


def get_lat_long(country, city):
    geolocator = Nominatim(user_agent='geoapiExercise')
    location = geolocator.geocode(f'{city},{country}')

    if location:
        return location.latitude, location.longitude
    return None


def transform_wikipedia_data(**kwargs):
    data = kwargs['ti'].xcom_pull(key='rows', task_ids='extract_data_from_wikipedia')
    data = json.loads(data)
    stadiums_df = pd.DataFrame(data)
    stadiums_df['location'] = stadiums_df.apply(lambda x: get_lat_long(x['country'], x['stadium']), axis=1)
    stadiums_df['images'] = stadiums_df['images'].apply(lambda x: x if x not in ['NO_IMAGE', '', None] else NO_IMAGE)
    stadiums_df['capacity'] = stadiums_df['capacity'].astype(int)
    # handle the duplicates
    duplicates = stadiums_df[stadiums_df.duplicated(['location'])]
    duplicates['location'] = duplicates.apply(lambda x: get_lat_long(x['country'], x['city']), axis=1)
    stadiums_df.update(duplicates)

    # push to xcom
    kwargs['ti'].xcom_push(key='rows', value=stadiums_df.to_json())

    return "OK"


def write_wikipedia_data(**kwargs):
    data = kwargs['ti'].xcom_pull(key='rows', task_ids='transform_wikipedia_data')

    data = json.loads(data)
    data = pd.DataFrame(data)
    file_name = ('stadiums_cleaned' + str(datetime.now().date()) + "_" + str(datetime.now().time())
                 .replace(":", ",") + ".csv")
    data.to_csv('abfs://footballdataengineering@footballdataengineering.dfs.core.windows.net/data/' + file_name, storage_options={
        'account_key': ''
    },index=False)


