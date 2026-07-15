import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from langchain.tools import tool
from tools.write_results import write_results_file

load_dotenv()
OPEN_DATA_APP_TOKEN = os.getenv("OPEN_DATA_APP_TOKEN")

def search_address_crash(address: str = None, coordinate_boundaries: dict=None, start_date: str = None, end_date: str = None, write_results: bool = False
) -> str:
    """Search for any recent car crash locations by address or coordinate boundaries.

    Args:
        address: optional, The building address in all-caps format (e.g., '1601 W CHICAGO AVE')
        start_date: Optional start date in YYYY-MM-DD format (e.g., '2024-01-01')
        end_date: Optional end date in YYYY-MM-DD format (e.g., '2024-12-31')
        write_results: Optional - set to true if the end user requests that files be saved

    Returns:
        A text summary including: details and date.
    """
    
    if not address and not coordinate_boundaries:
        raise Exception("Either coordinates or address is necessary to find a crash site")
    
    if not coordinate_boundaries:
      
        where_clause = " AND ".join(filter(None, [
            f"address='{address}'" if address else None
        ]))
    else:
        where_clause = f"latitude%20between%20{coordinate_boundaries['south']}%20and%20{coordinate_boundaries['north']}%20AND%20longitude%20between%20{coordinate_boundaries['west']}%20and%20{coordinate_boundaries['east']}"
        

    if start_date and end_date:
        where_clause += f" AND crash_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    elif start_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
        where_clause += f" AND crash_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    
    url = f"https://data.cityofchicago.org/resource/85ca-t3if.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            crashes = response.json()
            if write_results:
                write_results_file(crashes, outputname="crashes")

            # Format as string summary to make it easier for the LLM to understand
            summary = f"Found {len(crashes)} crashes for {address}:\n\n"
            for v in crashes:
                summary += f"  Crash address: {v.get('address', 'Unknown')}\n"
                summary += f"  Traffic control device in place: {v.get('traffic_control_device', 'Unknown')}\n"
                summary += f"  Traffic control device condition: {v.get('device_condition', 'Unknown')}\n"
                summary += f"  Weather: {v.get('weather_condition', 'Unknown')}\n"
                summary += f"  Lighting: {v.get('lighting_condition', 'Unknown')}\n"
                summary += f"  Date: {v.get('crash_date', 'Unknown')}\n"
                summary += f"  Road type: {v.get('trafficway_type', 'Unknown')}\n"
                summary += f"  Crash type: {v.get('crash_type', 'Unknown')}\n"
                summary += f"  Crash was related to an intersection: {v.get('intersection_related_i', 'Unknown')}\n"
                summary += f"  Crash was dooring of a cyclist: {v.get('dooring_i', 'Unknown')}\n"
                summary += f"  Total injuries: {v.get('injuries_total', 'Unknown')}\n"
                summary += f"  Most severe injury: {v.get('most_severe_injury', 'Unknown')}\n"
                summary += f"  Number of fatalities: {v.get('injuries_fatal', 'Unknown')}\n"

            if len(summary) > 10000:
                return summary[:10000] + "\n This query returned a huge amount of data and had to be truncated, so it's probably incomplete."

            else:
                return summary
        else:
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"
    
def search_coordinates_crash(coordinate_boundaries: dict, start_date: str = None, end_date: str = None, write_results: bool = False
) -> str:
    """Search for any results of recent car crashes within the bounds of a geocoordinate range.

    Args:
        coordinate_boundaries: The dict of the coordinate boundaries in format {"north":north_bound, "south":south_bound, "east":east_bound, "west": west_bound}
        start_date: Optional start date in YYYY-MM-DD format (e.g., '2024-01-01')
        end_date: Optional end date in YYYY-MM-DD format (e.g., '2024-12-31')
        write_results: Optional - set to true if the end user requests that files be saved

    Returns:
        A text summary including: details and date.
    """
    
    where_clause = f"latitude%20between%20{coordinate_boundaries['south']}%20and%20{coordinate_boundaries['north']}%20AND%20longitude%20between%20{coordinate_boundaries['west']}%20and%20{coordinate_boundaries['east']}"
        
    if start_date and end_date:
        where_clause += f" AND crash_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    elif start_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
        where_clause += f" AND crash_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    
    url = f"https://data.cityofchicago.org/resource/85ca-t3if.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            crashes = response.json()
            if write_results:
                write_results_file(crashes, outputname="crashes")

            # Format as string summary to make it easier for the LLM to understand
            summary = f"Found {len(crashes)} crashes:\n\n"
            for v in crashes:
                summary += f"  Crash Address: {v.get('street_no', 'Unknown')} {v.get('street_direction', 'Unknown')} {v.get('street_name', 'Unknown')}\n"
                summary += f"  Traffic control device in place: {v.get('traffic_control_device', 'Unknown')}\n"
                summary += f"  Traffic control device condition: {v.get('device_condition', 'Unknown')}\n"
                summary += f"  Weather: {v.get('weather_condition', 'Unknown')}\n"
                summary += f"  Lighting: {v.get('lighting_condition', 'Unknown')}\n"
                summary += f"  Date: {v.get('crash_date', 'Unknown')}\n"
                summary += f"  Road type: {v.get('trafficway_type', 'Unknown')}\n"
                summary += f"  Crash type: {v.get('crash_type', 'Unknown')}\n"
                summary += f"  Crash was related to an intersection: {v.get('intersection_related_i', 'Unknown')}\n"
                summary += f"  Crash was dooring of a cyclist: {v.get('dooring_i', 'Unknown')}\n"
                summary += f"  Total injuries: {v.get('injuries_total', 'Unknown')}\n"
                summary += f"  Most severe injury: {v.get('most_severe_injury', 'Unknown')}\n"
                summary += f"  Number of fatalities: {v.get('injuries_fatal', 'Unknown')}\n"
                summary += f"  Whether the incident was a hit-and-run: {v.get('hit_and_run_i', 'No')}\n"
                summary += f"  Latitude: {v.get('latitude', 'Unknown')}\n"
                summary += f"  Longitude: {v.get('longitude', 'Unknown')}\n"


            if len(summary) > 10000:
                return summary[:10000] + "\n This query returned a huge amount of data and had to be truncated, so it's probably incomplete."

            else:
                return summary
        else:
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"