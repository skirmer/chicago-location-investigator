
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
OPEN_DATA_APP_TOKEN = os.getenv("OPEN_DATA_APP_TOKEN")

def search_coordinates_violations(coordinate_boundaries:dict, start_date:str = None,  end_date: str = None):
    """Search for building code violations within the bounds of a set of geocoordinates (north, south, east, and west) with optional date filtering.
    Returns violation numbers and dates.

    Args:
        coordinate_boundaries: The dict of the coordinate boundaries in format {"north":north_bound, "south":south_bound, "east":east_bound, "west": west_bound}
        start_date: Optional start date in YYYY-MM-DD format (e.g., '2024-01-01')
        end_date: Optional end date in YYYY-MM-DD format (e.g., '2024-12-31')

    Returns:
        A text summary including: violation numbers, dates, and status
    """
    # Build where clause with date filtering if provided
    where_clause = f"latitude%20between%20{coordinate_boundaries['south']}%20and%20{coordinate_boundaries['north']}%20AND%20longitude%20between%20{coordinate_boundaries['west']}%20and%20{coordinate_boundaries['east']}"

    print(where_clause)
    print(f"Retrieving building violations within {coordinate_boundaries}")

    if start_date and end_date:
        where_clause += f" AND violation_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    elif start_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
        where_clause += f" AND violation_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")

    url = f"https://data.cityofchicago.org/resource/22u3-xenr.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"

    print(url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            inspections = response.json()
            violations = [
                x for x in inspections if x.get("inspection_status") == "FAILED"
            ]

            if not violations:
                return f"No violations found at {coordinate_boundaries} during date range selected."

            # Format as string summary to make it easier for the LLM to understand
            summary = f"Found {len(violations)} violation(s) at {coordinate_boundaries} during date range selected:\n\n"
            for v in violations:
                summary += f"- Violation #{v.get('id', 'N/A')}\n"
                summary += f"  Date: {v.get('violation_date', 'Unknown')}\n"
                summary += f"  Address: {v.get('address', 'Unknown')}\n"

            if len(summary) > 10000:
                return summary[:10000] + "\n This query returned a huge amount of data aand had to be truncated, so it's probably incomplete."

            else:
                return summary
        else:
            print(response)
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"


def search_address_violations(
    address: str, start_date: str = None, end_date: str = None
) -> str:
    """Search for building code violations at a specific address with optional date filtering.
    Returns violation numbers and dates.

    Args:
        address: The building address in all-caps format (e.g., '1601 W CHICAGO AVE')
        start_date: Optional start date in YYYY-MM-DD format (e.g., '2024-01-01')
        end_date: Optional end date in YYYY-MM-DD format (e.g., '2024-12-31')

    Returns:
        A text summary including: violation numbers, dates, and status
    """
    # Build where clause with date filtering if provided
    where_clause = f"address='{address}'"
    print(f"Retrieving building violations for address {address}")

    if start_date and end_date:
        where_clause += f" AND violation_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    elif start_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
        where_clause += f" AND violation_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")

    url = f"https://data.cityofchicago.org/resource/22u3-xenr.json?$where={where_clause}&$$app_token={OPEN_DATA_APP_TOKEN}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            inspections = response.json()
            violations = [
                x for x in inspections if x.get("inspection_status") == "FAILED"
            ]

            if not violations:
                return f"No violations found at {address} during date range selected."

            # Format as string summary to make it easier for the LLM to understand
            summary = f"Found {len(violations)} violation(s) at {address} during date range selected:\n\n"
            for v in violations:
                summary += f"- Violation #{v.get('id', 'N/A')}\n"
                summary += f"  Date: {v.get('violation_date', 'Unknown')}\n"

            if len(summary) > 10000:
                return summary[:10000] + "\n This query returned a huge amount of data aand had to be truncated, so it's probably incomplete."

            else:
                return summary
        else:
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"


def get_violation_details(violation_id_number: str) -> str:
    """Get detailed information about a specific violation by its violation number.

    Args:
        violation_id_number: The violation number from a previous search (e.g., '12345678')

    Returns:
        Detailed information about the specific violation including description and inspector notes
    """
    url = f"https://data.cityofchicago.org/resource/22u3-xenr.json?id={violation_id_number}&$$app_token={OPEN_DATA_APP_TOKEN}"

    print(f"Retrieving details for violation #{violation_id_number}")

    try:
        response = requests.get(url)
        if response.status_code == 200:
            violations = response.json()
            if not violations:
                return f"No inspection found with number {violation_id_number}"

            record = violations[0]
            details = f"Violation #{violation_id_number} Details:"
            details = f"Inspection #{record.get('inspection_number', 'N/A')}\n\n"
            details += f"Address: {record.get('address', 'N/A')}\n"
            details += f"Status: {record.get('inspection_status', 'N/A')}\n"
            details += f"Violation Status: {record.get('violation_status', 'N/A')}"
            details += f"Violation Date: {record.get('violation_date', 'N/A')}\n"
            details += f"Inspector Comments: {record.get('violation_inspector_comments', 'N/A')} \n"
            details += f"Violation Description: {record.get('violation_description', 'N/A')} \n\n"

            details += "Violation status notes: Open means it has not been remedied, Complied means it has been remedied."
            details += f"\n Today's date is {datetime.now().strftime('%Y-%m-%d')}"

            if len(details) > 10000:
                return details[:10000] + "\n This query returned a huge amount of data aand had to be truncated, so it's probably incomplete."

            else:
                return details
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"
