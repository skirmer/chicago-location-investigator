# Orchestration for agent

from langchain.agents import create_agent
import os

from tools.tools_geocoding import geocode_address, get_proximity_to_coords

from tools.tools_violations import search_address_violations, get_violation_details, search_coordinates_violations

from tools.tools_permits import search_address_active_building_permits, search_coordinates_active_building_permits
from tools.tools_art import search_coordinates_murals
from tools.tools_food import search_address_food_inspections, search_coordinates_food_inspections
from models.ollama import model as model_llama3_1
from models.anthropic import model as model_anthropic

from dotenv import load_dotenv
import argparse

load_dotenv()
OPEN_DATA_APP_TOKEN = os.getenv("OPEN_DATA_APP_TOKEN")


def setup(model):
    agent = create_agent(
        model=model,
        tools=[search_address_violations, get_violation_details, search_address_active_building_permits, search_address_food_inspections, geocode_address, get_proximity_to_coords, search_coordinates_violations, search_coordinates_active_building_permits, search_coordinates_food_inspections, search_coordinates_murals],
        system_prompt="""You are a research assistant helping users find information about buildings in Chicago, Illinois. They will submit an address, and possibly a date or date range to look for.

    When addresses are provided, convert them to all-caps and format cardinal directions with one letter (eg, N for North) and abbreviate street types (eg, BLVD for Boulevard). Where restaurant names are provided, also convert them to all-caps before passing to a tool.

    Available tools:
    1. geocode_address - If the question involves looking around the vicinity of an address, not the specific address itself, geocode that address to get coordinates.
    2. get_proximity_to_coords - This function takes in coordinates representing an address and calculates the north, south, east, and west bounds for the requested radius. Radius must be provided in miles.
    3. search_address_violations - Get building code violations for an exact address with optional date filtering (start_date, end_date, or days parameters)
    4. get_violation_details - Get detailed info about a specific building code violation number. Submit one violation number at a time with argument "violation_id_number".
    5. search_address_active_building_permits - Get a listing of any active building permits for an address.
    6. search_coordinates_active_building_permits - Get a listing of any active building permits found within coordinate boundaries.
    7. search_address_food_inspections - Get a listing of health department inspections for restaurants or food services. Accepts name and/or address.
    8. search_coordinates_food_inspections - Get a listing of health department inspections for restaurants or food services found within coordinate boundaries.
    9. search_coordinates_violations - Get a listing of building code violations within coordinate boundaries.
    10. search_coordinates_murals - Get a listing of public art murals on buildings within coordinate boundaries.

    Use multiple tools when helpful to provide comprehensive answers. Do not ask follow up questions or offer to do more. If results had to be truncated due to length, let the user know.""",
    )
    return agent

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Query building code violations in Chicago')
    parser.add_argument('-m', '--model_name', type=str, required=False, help='The LLM to use to run the agent', default='llama3.1')    
    parser.add_argument('-q', '--query', type=str, required=False, help='The query to ask about building violations')
    parser.add_argument('-d', '--debug', type=str, required=False, help='Whether you want to run the job in debug mode, getting all the model exchanges')
    args = parser.parse_args()
    
    if args.query:
        query_text = args.query
    else:
        query_text = "Find all the building code violations from 2025 within .1 mile of 1751 West Augusta Blvd, and check and see if any of the addresses have active building permits. Tell me what the violations are, and list the building permits so I can see if the permits might be remediating the violations."
        # query_text = "Suggest two restaurants within .25 mile of 1751 West Augusta blvd that have not failed a health inspection since November 1, 2025"
        # query_text = "What building code violations have been recorded for 1601 West Chicago Avenue since June 2025? Describe what they were for, and indicate how long they have been open."

    if args.model_name == "llama3.1":
        print("Using model Llama 3.1")
        model = model_llama3_1
    elif args.model_name == 'claude':
        print("Using model Claude Haiku 4.5")
        model = model_anthropic
    else:
        print("No supported model provided, defaulting to Llama 3.1")
        model = model_llama3_1

    agent = setup(model)

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
    
    if args.debug:
        for message in response["messages"]:
            print(f"\n{message.type.upper()}: {message.content}")
