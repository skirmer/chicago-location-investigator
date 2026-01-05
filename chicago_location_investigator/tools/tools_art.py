
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
OPEN_DATA_APP_TOKEN = os.getenv("OPEN_DATA_APP_TOKEN")



def search_coordinates_murals(coordinate_boundaries:dict, start_date:str = None,  end_date: str = None):
    """Search for public murals within the bounds of a set of geocoordinates (north, south, east, and west) with optional date filtering on the date the work was created.

    Args:
        coordinate_boundaries: The dict of the coordinate boundaries in format {"north":north_bound, "south":south_bound, "east":east_bound, "west": west_bound}
        start_date: Optional start date in YYYY-MM-DD format (e.g., '2024-01-01')
        end_date: Optional end date in YYYY-MM-DD format (e.g., '2024-12-31')

    Returns:
        A text summary including: artist name/credit, artwork title, year installed, medium, and street address
    """
    # Build where clause with date filtering if provided
    where_clause = f"latitude%20between%20{coordinate_boundaries['south']}%20and%20{coordinate_boundaries['north']}%20AND%20longitude%20between%20{coordinate_boundaries['west']}%20and%20{coordinate_boundaries['east']}"

    print(f"Retrieving public murals within {coordinate_boundaries}")

    if start_date and end_date:
        where_clause += f" AND violation_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    elif start_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
        where_clause += f" AND violation_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")

    url = f"https://data.cityofchicago.org/resource/we8h-apcf.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            murals = response.json()

            if not murals:
                return f"No murals found at {coordinate_boundaries} during date range selected."

            # Format as string summary to make it easier for the LLM to understand
            summary = f"Found {len(murals)} mural(s) at {coordinate_boundaries} during date range selected:\n\n"
            for v in murals:
                summary += f"- Mural Registration ID #{v.get('mural_registration_id', 'N/A')}\n"
                summary += f"  Year Installed: {v.get('year_installed', 'Unknown')}\n"
                summary += f"  Artist Credit: {v.get('artist_credit', 'Unknown')}\n"
                summary += f"  Artwork Title: {v.get('artwork_title', 'Unknown')}\n"
                summary += f"  Location Description: {v.get('location_description', 'Unknown')}\n"
                summary += f"  Street Address: {v.get('street_address', 'Unknown')}\n"
                summary += f"  Description: {v.get('description', 'Unknown')}\n"
                summary += f"  Media: {v.get('media', 'Unknown')}\n"
                summary += f"  Organization: {v.get('affiliated_or_commissioning', 'Unknown')}\n"
                

            if len(summary) > 10000:
                return summary[:10000] + "\n This query returned a huge amount of data and had to be truncated, so it's probably incomplete."

            else:
                return summary
        else:
            print(response)
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

