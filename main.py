# Orchestration for agent

from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
import os

from tools.tools_geocoding import geocode_address, get_proximity_to_coords

from tools.tools_violations import search_address_violations, get_violation_details, search_coordinates_violations

from tools.tools_permits import search_address_active_building_permits, search_coordinates_active_building_permits

from tools.tools_food import search_address_food_inspections, search_coordinates_food_inspections

from dotenv import load_dotenv
import argparse

load_dotenv()
YOUR_APP_TOKEN = os.getenv("YOUR_APP_TOKEN")

if __name__ == "__main__":
    model = ChatAnthropic(
        temperature=0,
        model="claude-haiku-4-5",
    )

    agent = create_agent(
        model=model,
        tools=[search_address_violations, get_violation_details, search_address_active_building_permits, search_address_food_inspections, geocode_address, get_proximity_to_coords, search_coordinates_violations, search_coordinates_active_building_permits, search_coordinates_food_inspections],
        system_prompt="""You are a research assistant helping users find information about buildings in Chicago, Illinois. They will submit an address, and possibly a date or date range to look for.

    When addresses are provided, convert them to all-caps and format cardinal directions with one letter (eg, N for North) and abbreviate street types (eg, BLVD for Boulevard).

    Available tools:
    1. geocode_address - If the question involves looking around the vicinity of an address, geocode that address to get coordinates.
    2. get_proximity_to_coords - This function takes in coordinates of an address and calculates the north, south, east, and west bounds for the requested radius. Radius must be provided in miles.
    3. search_address_violations - Get building code violations for an address with optional date filtering (start_date, end_date, or days parameters)
    4. get_violation_details - Get detailed info about a specific building code violation number
    5. search_address_active_building_permits - Get a listing of any active building permits for an address.
    6. search_coordinates_active_building_permits - Get a listing of any active building permits found within coordinate boundaries.
    7. search_address_food_inspections - Get a listing of health department inspections for restaurants or food services. Accepts name and/or address.
    8. search_coordinates_food_inspections - Get a listing of health department inspections for restaurants or food services found within coordinate boundaries.

    Use multiple tools when helpful to provide comprehensive answers. Do not ask follow up questions or offer to do more. If results had to be truncated due to length, let the user know.""",
    )

    parser = argparse.ArgumentParser(description='Query building code violations in Chicago')
    parser.add_argument('--query', type=str, required=False, help='The query to ask about building violations')
    args = parser.parse_args()
    
    if args.query:
        query_text = args.query
    else:
        query_text = "What do you know about the restaurants within a .25 mile radius of 1751 West Augusta Blvd? Are there any that have bad results from health inspections since November 2025?"
        # query_text = "What building code violations have been recorded for 1601 West Chicago Avenue since June 2025? Describe what they were for, and indicate how long they have been open."


    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": query_text,
                }
            ]
        }
    )

    print(response["messages"][-1].content)
    for message in response["messages"]:
        print(f"\n{message.type.upper()}: {message.content}")
