import requests
import os
from dotenv import load_dotenv

load_dotenv()
OPEN_DATA_APP_TOKEN = os.getenv("OPEN_DATA_APP_TOKEN")

def search_ward_for_point(latitude: float, longitude: float) -> str:
    """Identify which Chicago ward contains a specific geocoordinate point.

    Args:
        latitude: The latitude of the point (e.g., 41.9012)
        longitude: The longitude of the point (e.g., -87.6743)

    Returns:
        A text summary naming the ward the point falls within.
    """
    # NOTE: WKT is 'POINT (longitude latitude)' — longitude FIRST.
    where_clause = f"intersects(the_geom, 'POINT ({longitude} {latitude})')"
    url = f"https://data.cityofchicago.org/resource/p293-wvbd.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            wards = response.json()
            if not wards:
                return f"No ward found containing point ({latitude}, {longitude})."
            w = wards[0]
            return f"Point ({latitude}, {longitude}) is in Ward {w.get('ward', 'Unknown')}."
        else:
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"
