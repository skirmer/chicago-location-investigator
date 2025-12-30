
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
OPEN_DATA_APP_TOKEN = os.getenv("OPEN_DATA_APP_TOKEN")


def search_address_active_building_permits(house_number:str, cardinal_direction: str, street: str) -> str:
    """Search for active building permits issued for a specific address.
    Returns permit details.

    Args:
        house_number: The number of the house or building on that street (e.g., "123")
        cardinal_direction: The direction of the street, single character, in all caps format. One of N, S, E, or W.
        street: The street name in all-caps format (e.g., 'MAIN ST')
       
    Returns:
        A text summary including: permit number, status
    """
    
    # Build where clause with date filtering if provided
    where_clause = f"street_name='{street}' AND street_number='{house_number}' AND street_direction='{cardinal_direction}'"
    print(f"Retrieving active permits for address {house_number} {cardinal_direction} {street}")

    url = f"https://data.cityofchicago.org/resource/ydr8-5enu.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            permits = response.json()

            active_permits = [
                x for x in permits if x.get("permit_status") == "ACTIVE"
            ]

            if not active_permits:
                return f"No active permits found for {house_number} {cardinal_direction} {street}."

            # Format as string summary to make it easier for the LLM to understand
            summary = f"Found {len(active_permits)} active permit(s) issued for {house_number} {cardinal_direction} {street}:\n\n"
            for v in active_permits:
                summary += f"- Permit #{v.get('permit#', 'N/A')}\n"
                summary += f"  Permit Type: {v.get('permit_type', 'N/A')}"
                summary += f"  Date: {v.get('issue_date', 'Unknown')}\n"
                summary += f"  Work Description: {v.get('work_description', 'Unknown')}\n"
                summary += f"  Issued To: {v.get('contact_1_name', 'Unknown')}\n\n"

            if len(summary) > 10000:
                return summary[:10000] + "\n This query returned a huge amount of data aand had to be truncated, so it's probably incomplete."

            else:
                return summary
        else:
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"
    

def search_coordinates_active_building_permits(coordinate_boundaries:dict) -> str:
    """Search for active building permits issued within a set of coordinates.
    Returns permit details.

    Args:
        coordinate_boundaries: The dict of the coordinate boundaries in format {"north":north_bound, "south":south_bound, "east":east_bound, "west": west_bound}
       
    Returns:
        A text summary including: permit number, status, and address
    """
    
    # Build where clause with date filtering if provided
    where_clause = f"latitude%20between%20{coordinate_boundaries['south']}%20and%20{coordinate_boundaries['north']}%20AND%20longitude%20between%20{coordinate_boundaries['west']}%20and%20{coordinate_boundaries['east']}"

    print(f"Retrieving active permits within {coordinate_boundaries}")

    url = f"https://data.cityofchicago.org/resource/ydr8-5enu.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            permits = response.json()
            active_permits = [
                x for x in permits if x.get("permit_status") == "ACTIVE"
            ]

            if not active_permits:
                return f"No active permits found within {coordinate_boundaries}."

            # Format as string summary to make it easier for the LLM to understand
            summary = f"Found {len(active_permits)} active permit(s) issued in {coordinate_boundaries}:\n\n"
            for v in active_permits:
                summary += f"- Permit #{v.get('permit_', 'N/A')}\n"
                summary += f"  Permit Type: {v.get('permit_type', 'N/A')}"
                summary += f"  Date: {v.get('issue_date', 'Unknown')}\n"
                summary += f"  Work Description: {v.get('work_description', 'Unknown')}\n"
                summary += f"  Issued To: {v.get('contact_1_name', 'Unknown')}\n"
                summary += f"  Address: {v.get('street_number')} {v.get('street_direction')} {v.get('street_name')}\n\n"

            if len(summary) > 10000:
                return summary[:10000] + "\n This query returned a huge amount of data and had to be truncated, so it's probably incomplete."

            else:
                return summary
        else:
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"
    