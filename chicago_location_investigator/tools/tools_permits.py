
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from chicago_location_investigator.tools.data_model import LocationInput, ExactAddress, ExactCoordinates, CoordinateBoundaries

load_dotenv()
OPEN_DATA_APP_TOKEN = os.getenv("OPEN_DATA_APP_TOKEN")


def search_active_building_permits(location:LocationInput) -> str:
    """Search for active building permits issued for a specific address.
    Returns permit details.

    Args:
        location:
            location_type = "exact_address"
                value.address, value.house_number, value.street_direction, and value.street must be provided
            location_type = "coordinate_boundaries"
                value.coordinate_boundaries must be provided   
       
    Returns:
        A text summary including: permit number, status, and address
    """
    
    # Build where clause with date filtering if provided
    if isinstance(location.value, ExactAddress):
        where_clause = f"street_name='{location.value.street}' AND street_number='{location.value.house_number}' AND street_direction='{location.value.street_direction}'"
    elif isinstance(location.value, CoordinateBoundaries):
        where_clause = f"latitude%20between%20{location.value.coordinate_boundaries['south']}%20and%20{location.value.coordinate_boundaries['north']}%20AND%20longitude%20between%20{location.value.coordinate_boundaries['west']}%20and%20{location.value.coordinate_boundaries['east']}"
    else:
        print("Malformed input provided")

    print(f"Retrieving active permits for address {location.value}")

    url = f"https://data.cityofchicago.org/resource/ydr8-5enu.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            permits = response.json()

            active_permits = [
                x for x in permits if x.get("permit_status") == "ACTIVE"
            ]

            if not active_permits:
                return f"No active permits found for {location.value}."

            # Format as string summary to make it easier for the LLM to understand
            summary = f"Found {len(active_permits)} active permit(s) issued for {location.value}:\n\n"
            for v in active_permits:
                summary += f"- Permit #{v.get('permit#', 'N/A')}\n"
                summary += f"  Permit Type: {v.get('permit_type', 'N/A')}"
                summary += f"  Date: {v.get('issue_date', 'Unknown')}\n"
                summary += f"  Work Description: {v.get('work_description', 'Unknown')}\n"
                summary += f"  Issued To: {v.get('contact_1_name', 'Unknown')}\n\n"
                summary += f"  Address: {v.get('street_number')} {v.get('street_direction')} {v.get('street_name')}\n\n"

            if len(summary) > 10000:
                return summary[:10000] + "\n This query returned a huge amount of data and had to be truncated, so it's probably incomplete."

            else:
                return summary
        else:
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"
    

# def search_coordinates_active_building_permits(location:LocationInput) -> str:
#     """Search for active building permits issued within a set of coordinates.
#     Returns permit details.

#     Args:
#         location:
#             location_type = "coordinate_boundaries"
#                 value.coordinate_boundaries must be provided   
#     Returns:
#         A text summary including: permit number, status, and address
#     """
    
#     # Build where clause with date filtering if provided
#     if isinstance(location.value, CoordinateBoundaries):
#         where_clause = f"latitude%20between%20{location.value.coordinate_boundaries['south']}%20and%20{location.value.coordinate_boundaries['north']}%20AND%20longitude%20between%20{location.value.coordinate_boundaries['west']}%20and%20{location.value.coordinate_boundaries['east']}"
#     else:
#         print("Malformed input provided")
        
#     print(f"Retrieving active permits within {location.value}")

#     url = f"https://data.cityofchicago.org/resource/ydr8-5enu.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"
#     try:
#         response = requests.get(url)
#         if response.status_code == 200:
#             permits = response.json()
#             active_permits = [
#                 x for x in permits if x.get("permit_status") == "ACTIVE"
#             ]

#             if not active_permits:
#                 return f"No active permits found within {location.value}."

#             # Format as string summary to make it easier for the LLM to understand
#             summary = f"Found {len(active_permits)} active permit(s) issued in {location.value}:\n\n"
#             for v in active_permits:
#                 summary += f"- Permit #{v.get('permit_', 'N/A')}\n"
#                 summary += f"  Permit Type: {v.get('permit_type', 'N/A')}"
#                 summary += f"  Date: {v.get('issue_date', 'Unknown')}\n"
#                 summary += f"  Work Description: {v.get('work_description', 'Unknown')}\n"
#                 summary += f"  Issued To: {v.get('contact_1_name', 'Unknown')}\n"
#                 summary += f"  Address: {v.get('street_number')} {v.get('street_direction')} {v.get('street_name')}\n\n"

#             if len(summary) > 10000:
#                 return summary[:10000] + "\n This query returned a huge amount of data and had to be truncated, so it's probably incomplete."

#             else:
#                 return summary
#         else:
#             return f"Error retrieving data: {response.status_code}"
#     except Exception as e:
#         return f"Error: {e}"
    