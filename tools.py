import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
YOUR_APP_TOKEN = os.getenv("YOUR_APP_TOKEN")


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

    url = f"https://data.cityofchicago.org/resource/22u3-xenr.json?$where={where_clause}&$$app_token={YOUR_APP_TOKEN}"

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
    url = f"https://data.cityofchicago.org/resource/22u3-xenr.json?id={violation_id_number}&$$app_token={YOUR_APP_TOKEN}"

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

            return details
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"


def get_active_building_permits(house_number:str, cardinal_direction: str, street: str) -> str:
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

    url = f"https://data.cityofchicago.org/resource/ydr8-5enu.json?$where={where_clause}&$$app_token={YOUR_APP_TOKEN}"
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
                summary += f"  Issued To: {v.get('contact_1_name', 'Unknown')}\n"

            return summary
        else:
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"
    
    
def get_food_inspections(name: str = None, address: str = None, start_date: str = None, end_date: str = None
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
    
    if not address and not name:
        raise Exception("Either name or address is necessary to find a restaurant")
    address_or_name = " ".join(filter(None, [name, address]))
    
    where_clause = " AND ".join(filter(None, [
        f"dba_name='{name}'" if name else None,
        f"address='{address}'" if address else None
    ]))
    if start_date and end_date:
        where_clause += f" AND inspection_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    elif start_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
        where_clause += f" AND inspection_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
        print(f"Date range: {start_date} - {end_date}")
    
    url = f"https://data.cityofchicago.org/resource/4ijn-s7e5.json?$where={where_clause}&$$app_token={YOUR_APP_TOKEN}"
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

            return summary
        else:
            return f"Error retrieving data: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"