import requests
import pandas as pd
from sqlalchemy import create_engine

# --- CONFIGURATION ---
API_KEY = '7d25aace-475d-460a-a348-468d60633466'  # Replace with your API key
API_URL = f"http://api.airvisual.com/v2/cities?state=California&country=USA&key={API_KEY}"

# PostgreSQL setup
DB_USER = 'postgres'
DB_PASS = 'ABCD'           # Replace with your DB password
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'airquality_db'
TABLE_NAME = 'air_quality_data'

# --- EXTRACT ---
def fetch_air_quality_data():
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
    cities = data['data']

    records = []
    for city in cities[:1]:  # Fetch only first 40
        city_name = city['city']
        details_url = f"http://api.airvisual.com/v2/city?city={city_name}&state=California&country=USA&key={API_KEY}"
        details_response = requests.get(details_url)
        if details_response.status_code != 200:
            continue
        city_data = details_response.json()
        if 'data' not in city_data:
            continue
        pollution = city_data['data'].get('current', {}).get('pollution', {})
        weather = city_data['data'].get('current', {}).get('weather', {})

        record = {
            'city': city_name,
            'aqi_us': pollution.get('aqius'),
            'main_pollutant': pollution.get('mainus'),
            'temperature': weather.get('tp'),
            'humidity': weather.get('hu'),
            'wind_speed': weather.get('ws'),
            'timestamp': pollution.get('ts'),
            'pressure': weather.get('pr'),
            'icon': weather.get('ic'),
            'geo': str(city_data['data']['location']['coordinates']),
        }
        records.append(record)

    return pd.DataFrame(records)

# --- TRANSFORM ---
def clean_data(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.dropna(inplace=True)
    return df

# --- LOAD ---
def load_to_postgres(df):
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    df.to_sql(TABLE_NAME, engine, if_exists='replace', index=False)
    print("Data loaded to PostgreSQL successfully.")

# --- MAIN ---
if __name__ == '__main__':
    df = fetch_air_quality_data()
    df = clean_data(df)
    load_to_postgres(df)
    print("Preview of loaded data:")
    print(df.head())
