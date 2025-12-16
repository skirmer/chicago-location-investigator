import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()
OPEN_DATA_APP_TOKEN = os.getenv("OPEN_DATA_APP_TOKEN")

def search_address_food_inspections(name: str = None, address: str = None, coordinate_boundaries: dict=None, start_date: str = None, end_date: str = None
) -> str:
    """Search for any results of recent health department inspections of restaurants by address or name.

    Args:
        address: optional, The building address in all-caps format (e.g., '1601 W CHICAGO AVE')
        name: optional, the business name
        start_date: Optional start date in YYYY-MM-DD format (e.g., '2024-01-01')
        end_date: Optional end date in YYYY-MM-DD format (e.g., '2024-12-31')

    Returns:
        A text summary including: details and date.
    """
    
    if not address and not name and not coordinate_boundaries:
        raise Exception("Either name, coordinates, or address is necessary to find a restaurant")
    
    if not coordinate_boundaries:
        address_or_name = " ".join(filter(None, [name, address]))
        
        where_clause = " AND ".join(filter(None, [
            f"dba_name='{name}'" if name else None,
            f"address='{address}'" if address else None
        ]))
    else:
        where_clause = f"latitude%20between%20{coordinate_boundaries['south']}%20and%20{coordinate_boundaries['north']}%20AND%20longitude%20between%20{coordinate_boundaries['west']}%20and%20{coordinate_boundaries['east']}"
        

    if start_date and end_date:
        where_clause += f" AND inspection_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    elif start_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
        where_clause += f" AND inspection_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    
    url = f"https://data.cityofchicago.org/resource/4ijn-s7e5.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            inspections = response.json()

            # Format as string summary to make it easier for the LLM to understand
            summary = f"Found {len(inspections)} inspections for {address_or_name}:\n\n"
            for v in inspections:
                summary += f"  Business name: {v.get('dba_name', 'Unknown')}\n"
                summary += f"  Business address: {v.get('address', 'Unknown')}\n"
                summary += f"  Results: {v.get('results', 'Unknown')}\n"
                summary += f"  Date: {v.get('inspection_date', 'Unknown')}\n"
                summary += f"  Violation: {v.get('violations', 'Unknown')}\n"
                summary += f"  Risk Level: {v.get('risk', 'Unknown')}\n"

            if len(summary) > 10000:
                return summary[:10000] + "\n This query returned a huge amount of data and had to be truncated, so it's probably incomplete."

            else:
                return summary
        else:
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"
    
def search_coordinates_food_inspections(coordinate_boundaries: dict, type: str=None, start_date: str = None, end_date: str = None
) -> str:
    """Search for any results of recent health department inspections of restaurants within the bounds of a geocoordinate range.

    Args:
        coordinate_boundaries: The dict of the coordinate boundaries in format {"north":north_bound, "south":south_bound, "east":east_bound, "west": west_bound}
        start_date: Optional start date in YYYY-MM-DD format (e.g., '2024-01-01')
        end_date: Optional end date in YYYY-MM-DD format (e.g., '2024-12-31')
        type: Optional, indicate the type of results desired. Options: "Fail", "Pass"

    Returns:
        A text summary including: details and date.
    """
    
    where_clause = f"latitude%20between%20{coordinate_boundaries['south']}%20and%20{coordinate_boundaries['north']}%20AND%20longitude%20between%20{coordinate_boundaries['west']}%20and%20{coordinate_boundaries['east']}"
        
    if start_date and end_date:
        where_clause += f" AND inspection_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    elif start_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
        where_clause += f" AND inspection_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
        
    if type:
        where_clause += f" AND results='{type}'"
        
    
    url = f"https://data.cityofchicago.org/resource/4ijn-s7e5.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            inspections = response.json()

            # Format as string summary to make it easier for the LLM to understand
            summary = f"Found {len(inspections)} inspections:\n\n"
            for v in inspections:
                summary += f"  Business name: {v.get('dba_name', 'Unknown')}\n"
                summary += f"  Business address: {v.get('address', 'Unknown')}\n"
                summary += f"  Results: {v.get('results', 'Unknown')}\n"
                summary += f"  Date: {v.get('inspection_date', 'Unknown')}\n"
                summary += f"  Violation: {v.get('violations', 'Unknown')}\n"

            if len(summary) > 10000:
                return summary[:10000] + "\n This query returned a huge amount of data and had to be truncated, so it's probably incomplete."

            else:
                return summary
        else:
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"