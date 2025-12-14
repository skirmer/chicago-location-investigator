import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
import pytest

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent))

# Because the LLM is not deterministic, I may want to run tests several times to get a representative sample of behavior
num_runs = 1


MOCK_SEARCH_RESPONSE = [
        {
            "id": "12345",
            "violation_date": "2023-01-01",
            "inspection_status": "FAILED"
        },
        {
            "id": "12365",
            "violation_date": "2023-02-01",
            "inspection_status": "FAILED"
        }        
    ]
    
MOCK_DETAILS_RESPONSE = [
    {
        "id": "12345",
        "address": "123 N MAIN ST",
        "inspection_status": "FAILED",
        "violation_date": "2023-01-01",
        "violation_inspector_comments": "Missing door frame",
        "violation_description": "MAINTAIN DOOR",
        "violation_status": "Open"
    }
]

MOCK_DETAILS_RESPONSE2 = [
    {
        "id": "12365",
        "address": "123 N MAIN ST",
        "inspection_status": "FAILED",
        "violation_date": "2023-02-01",
        "violation_inspector_comments": "Electrical problems, wires loose and sparking",
        "violation_description": "ELECTRICAL",
        "violation_status": "Open"
    }
]

system_prompt = """You are a research assistant helping users find information about buildings in Chicago, Illinois. They will submit an address, and possibly a date or date range to look for.

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

    Use multiple tools when helpful to provide comprehensive answers. Do not ask follow up questions or offer to do more."""

@pytest.fixture
def agent():

    from tools.tools_geocoding import geocode_address, get_proximity_to_coords

    from tools.tools_violations import search_address_violations, get_violation_details, search_coordinates_violations

    from tools.tools_permits import search_address_active_building_permits, search_coordinates_active_building_permits

    from tools.tools_food import search_address_food_inspections, search_coordinates_food_inspections

    model = ChatAnthropic(model="claude-haiku-4-5")
    return create_agent(
        model=model,
        tools=[search_address_violations, get_violation_details, search_address_active_building_permits, search_address_food_inspections, geocode_address, get_proximity_to_coords, search_coordinates_violations, search_coordinates_active_building_permits, search_coordinates_food_inspections],
        system_prompt=system_prompt
        )

@pytest.mark.parametrize("run", range(num_runs))
@patch('tools.tools_violations.requests.get')
def test_agent_formats_address_correctly(mock_get, agent, run):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_DETAILS_RESPONSE
    mock_get.return_value = mock_response
    
    response = agent.invoke(
            {"messages": [{"role": "user", "content": "What violations are at 123 north main street?"}]}
        )
    
    assert mock_get.called is True
    first_call_url = mock_get.call_args_list[0][0][0]
    print(first_call_url)
    assert "123 N MAIN ST" in first_call_url
    assert len(response['messages']) > 0
    

@pytest.mark.parametrize("run", range(num_runs))
@patch('tools.tools_violations.requests.get')
def test_agent_formats_address_correctly2(mock_get, agent, run):
    """If the address has no direction or no street type, it should still work"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_DETAILS_RESPONSE
    mock_get.return_value = mock_response
    
    response = agent.invoke(
            {"messages": [{"role": "user", "content": "What violations are at 123 Main Street?"}]}
        )
    
    assert mock_get.called is True
    first_call_url = mock_get.call_args_list[0][0][0]
    print(first_call_url)
    assert "123 MAIN ST" in first_call_url
    assert len(response['messages']) > 0

@pytest.mark.parametrize("run", range(num_runs))
@patch('tools.tools_violations.requests.get')
def test_agent_formats_address_correctly3(mock_get, agent, run):

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_DETAILS_RESPONSE
    mock_get.return_value = mock_response
    
    response = agent.invoke(
            {"messages": [{"role": "user", "content": "What violations are at 123 North Main?"}]}
        )
    
    assert mock_get.called is True
    first_call_url = mock_get.call_args_list[0][0][0]
    print(first_call_url)
    assert "123 N MAIN" in first_call_url
    assert len(response['messages']) > 0    

    
def mock_multi_tool_response(url, *args, **kwargs):
    """Mock response handler for tests that call multiple tools."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    if "address=" in url:
        mock_response.json.return_value = MOCK_SEARCH_RESPONSE
    elif "id=" in url:
        mock_response.json.return_value = MOCK_DETAILS_RESPONSE
    
    return mock_response
 
@pytest.mark.parametrize("run", range(num_runs))
@patch('tools.tools_violations.requests.get')
def test_agent_calls_multiple_tools_in_order(mock_get, agent, run):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_DETAILS_RESPONSE
    mock_get.return_value = mock_response
    mock_get.side_effect = mock_multi_tool_response
    response = agent.invoke(
            {"messages": [{"role": "user", "content": "Show me violations at 123 north main street and give details about violation 12345"}]}
        )
    
    assert mock_get.call_count >= 2
    first_call_url = mock_get.call_args_list[0][0][0]
    print(first_call_url)
    assert "123 N MAIN ST" in first_call_url
    assert len(response['messages']) > 2

@pytest.mark.parametrize("run", range(num_runs))
@patch('tools.tools_violations.requests.get')
def test_agent_handles_date_filtering(mock_get, agent, run):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_SEARCH_RESPONSE
    mock_get.return_value = mock_response

    response = agent.invoke(
            {"messages": [{"role": "user", "content": "What violations happened at 123 north main street between January and March 2023?"}]}
        )
    first_call_url = mock_get.call_args_list[0][0][0]
    final_content = str(response["messages"][-1].content).lower()

    assert mock_get.called is True
    assert "violation_date" in first_call_url
    assert "violation" in final_content or "inspection" in final_content
    

def mock_violation_details_response(url, *args, **kwargs):
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    if "id=12345" in url:
        mock_response.json.return_value = MOCK_DETAILS_RESPONSE
    elif "id=12365" in url:
        mock_response.json.return_value = MOCK_DETAILS_RESPONSE2
    elif "address=" in url:
        mock_response.json.return_value = MOCK_SEARCH_RESPONSE

    return mock_response

    
@pytest.mark.parametrize("run", range(num_runs))
@patch('tools.tools_violations.requests.get')
def test_agent_handles_extra_detail_filtering(mock_get, agent, run):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_DETAILS_RESPONSE2
    mock_get.return_value = mock_response
    mock_get.side_effect = mock_violation_details_response
    
    response = agent.invoke(
            {"messages": [{"role": "user", "content": "What violations happened at 123 north main street between January and March 2023 that included electrical issues?"}]}
        )

    first_call_url = mock_get.call_args_list[0][0][0]
    second_call_url = mock_get.call_args_list[1][0][0]
    third_call_url = mock_get.call_args_list[2][0][0]
    final_content = str(response["messages"][-1].content).lower()
       
    assert mock_get.call_count >= 3
    assert "electrical" in final_content
    assert "address" in first_call_url
    assert "id=" in second_call_url
    assert "id=" in third_call_url
    
    
