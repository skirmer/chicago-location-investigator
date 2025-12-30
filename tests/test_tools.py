import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
import pytest

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent))

# No LLM Agent tests in this file


MOCK_SEARCH_RESPONSE = [
    {"id": "12345", "violation_date": "2023-01-01", "inspection_status": "FAILED"},
    {"id": "12365", "violation_date": "2023-02-01", "inspection_status": "FAILED"},
]

MOCK_DETAILS_RESPONSE = [
    {
        "id": "12345",
        "address": "123 N MAIN ST",
        "inspection_status": "FAILED",
        "violation_date": "2023-01-01",
        "violation_inspector_comments": "Missing door frame",
        "violation_description": "MAINTAIN DOOR",
        "violation_status": "Open",
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
        "violation_status": "Open",
    }
]

#================================================
# Tests for Building Code Violations tools
#================================================

@patch("chicago_location_investigator.tools.tools_violations.requests.get")
def test_get_violations_basic(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_SEARCH_RESPONSE
    mock_get.return_value = mock_response

    from chicago_location_investigator.tools.tools_violations import search_address_violations

    result = search_address_violations("123 N MAIN ST")

    assert "2023-01-01" in result
    assert "12345" in result


@patch("chicago_location_investigator.tools.tools_violations.requests.get")
def test_get_violation_details(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_DETAILS_RESPONSE
    mock_get.return_value = mock_response

    from chicago_location_investigator.tools.tools_violations import get_violation_details

    result = get_violation_details("123 N MAIN ST")

    assert "FAILED" in result
    assert "Missing door frame" in result


#================================================
# Tests for Food Inspection tools
#================================================
MOCK_FOOD_RESPONSE = [
    {
        "inspection_id": "2628003",
        "dba_name": "PUFFY CAKES",
        "aka_name": "PUFFY CAKES",
        "license_": "2952342",
        "facility_type": "Restaurant",
        "risk": "Risk 1 (High)",
        "address": "1651 W Chicago AVE",
        "city": "CHICAGO",
        "state": "IL",
        "zip": "60622",
        "inspection_date": "2025-12-04T00:00:00.000",
        "inspection_type": "Canvass Re-Inspection",
        "results": "Pass",
        "violations": "38. INSECTS, RODENTS, & ANIMALS NOT PRESENT - Comments:  6-202.15 Inspector Comments: OBSERVED A GAP ALONG BOTTOM OF FRONT DOOR MUST MAKE TIGHT FITTING.",
        "latitude": "41.895929604646255",
        "longitude": "-87.66935205442793",
        "location": {
            "latitude": "41.895929604646255",
            "longitude": "-87.66935205442793",
            "human_address": '{"address": "", "city": "", "state": "", "zip": ""}',
        },
    }
]


@patch("chicago_location_investigator.tools.tools_food.requests.get")
def test_get_food_details_address(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_FOOD_RESPONSE
    mock_get.return_value = mock_response

    from chicago_location_investigator.tools.tools_food import search_address_food_inspections

    result = search_address_food_inspections(address="1651 W CHICAGO AVE")

    assert "Pass" in result
    assert "INSECTS" in result


def test_get_food_details_address_missing():
    from chicago_location_investigator.tools.tools_food import search_address_food_inspections

    with pytest.raises(Exception) as excinfo:
        search_address_food_inspections()

    assert (
        "Either name, coordinates, or address is necessary to find a restaurant"
        in str(excinfo.value)
    )


@patch("chicago_location_investigator.tools.tools_food.requests.get")
def test_get_food_details_coords(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_FOOD_RESPONSE
    mock_get.return_value = mock_response

    from chicago_location_investigator.tools.tools_food import search_coordinates_food_inspections

    result = search_coordinates_food_inspections(
        coordinate_boundaries={
            "north": 41.9,
            "south": 41.8,
            "east": -87.7,
            "west": -87.6,
        }
    )

    assert "Pass" in result
    assert "INSECTS" in result


#================================================
# Tests for Geocoding tools
#================================================
def test_coord_proximity():
    from chicago_location_investigator.tools.tools_geocoding import get_proximity_to_coords

    result = get_proximity_to_coords(coordinates=(41.98365, -87.983745))
    assert result == {
        "north": 41.990886508476436,
        "south": 41.97641349152356,
        "east": -87.97400981831206,
        "west": -87.99348018168794,
    }



#================================================
# Tests for Building Permits tools
#================================================
MOCK_PERMIT_RESPONSE = [
    {
        "id": "3208190",
        "permit_": "100937623",
        "permit_status": "ACTIVE",
        "permit_milestone": "ACTIVE",
        "permit_type": "PERMIT - NEW CONSTRUCTION",
        "review_type": "SELF CERT",
        "application_start_date": "2021-10-01T00:00:00.000",
        "issue_date": "2021-10-01T00:00:00.000",
        "processing_time": "0",
        "street_number": "830",
        "street_direction": "N",
        "street_name": "MARSHFIELD AVE",
        "work_description": "ERECT NEW 3 STORY, III-A, 3DU APARTMENT BUILDING W/ BASEMENT AND ROOF DECK, STAIRWAY REAR OPEN DECK ON 1ST FLOOR, OPEN PORCH, AND DETACHED 1 STORY, III-A, 3 CAR GARAGE W/ ROOF DECK AS PER PLANS: SELF CERT 2019 CBC",
        "permit_condition": "EXISTING, 3 DU (100283135), 2005",
        "building_fee_paid": "2960.51",
        "zoning_fee_paid": "1575",
        "other_fee_paid": "626",
        "subtotal_paid": "5161.51",
        "building_fee_unpaid": "0",
        "zoning_fee_unpaid": "0",
        "other_fee_unpaid": "0",
        "subtotal_unpaid": "0",
        "building_fee_waived": "0",
        "building_fee_subtotal": "2960.51",
        "zoning_fee_subtotal": "1575",
        "other_fee_subtotal": "626",
        "zoning_fee_waived": "0",
        "other_fee_waived": "0",
        "subtotal_waived": "0",
        "total_fee": "5161.51",
        "contact_1_type": "SELF CERT ARCHITECT",
        "contact_1_name": "VARI, RONALD",
        "contact_1_city": "CHICAGO",
        "contact_1_state": "IL",
        "contact_1_zipcode": "60622-",
        "contact_2_type": "CONTRACTOR-ELECTRICAL",
        "contact_2_name": "SH ELECTRICAL CONTRACTORS INC.",
        "contact_2_city": "CHICAGO",
        "contact_2_state": "IL",
        "contact_2_zipcode": "60707-",
        "contact_3_type": "CONTRACTOR-GENERAL CONTRACTOR",
        "contact_3_name": "DESMOND BUILDERS",
        "contact_3_city": "CHICAGO",
        "contact_3_state": "IL",
        "contact_3_zipcode": "60643",
        "contact_4_type": "MASONRY CONTRACTOR",
        "contact_4_name": "PRO MC CONSTRUCTION, INC.",
        "contact_4_city": "EVERGREEN PARK",
        "contact_4_state": "IL",
        "contact_4_zipcode": "60805",
        "contact_5_type": "OWNER",
        "contact_5_name": "THE ALVERNA GROUP LLC",
        "contact_5_city": "CHICAGO",
        "contact_5_state": "IL",
        "contact_5_zipcode": "60643",
        "contact_6_type": "CONTRACTOR-PLUMBER/PLUMBING",
        "contact_6_name": "DEE PLUMBING & SEWER, INC.",
        "contact_6_city": "ALSIP",
        "contact_6_state": "IL",
        "contact_6_zipcode": "60803-",
        "contact_7_type": "CONTRACTOR-REFRIGERATION",
        "contact_7_name": "J HEATING AND AIR CONDITION",
        "contact_7_city": "DOWNERS GROVE",
        "contact_7_state": "IL",
        "contact_7_zipcode": "60516",
        "contact_8_type": "CONTRACTOR-VENTILATION",
        "contact_8_name": "J HEATING AND AIR CONDITION",
        "contact_8_city": "DOWNERS GROVE",
        "contact_8_state": "IL",
        "contact_8_zipcode": "60516",
        "reported_cost": "424000",
        "pin_list": "1706439028",
        "community_area": "24",
        "census_tract": "242100",
        "ward": "1",
        "xcoordinate": "1165200.0947457305",
        "ycoordinate": "1905760.3675452562",
        "latitude": "41.89700757335218",
        "longitude": "-87.66868964740345",
        "location": {
            "type": "Point",
            "coordinates": [-87.668689647403, 41.897007573352],
        },
    }
]


@patch("chicago_location_investigator.tools.tools_permits.requests.get")
def test_get_permit_details_address(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_PERMIT_RESPONSE
    mock_get.return_value = mock_response

    from chicago_location_investigator.tools.tools_permits import search_address_active_building_permits

    result = search_address_active_building_permits(house_number="830", cardinal_direction="N", street= "Marshfield Ave")

    assert "GARAGE W/ ROOF DECK" in result
    assert "PERMIT" in result

@patch("chicago_location_investigator.tools.tools_permits.requests.get")
def test_get_food_details_coords(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_PERMIT_RESPONSE
    mock_get.return_value = mock_response

    from chicago_location_investigator.tools.tools_permits import search_coordinates_active_building_permits

    result = search_coordinates_active_building_permits(
        coordinate_boundaries={
            "north": 41.9,
            "south": 41.8,
            "east": -87.7,
            "west": -87.6,
        }
    )

    assert "NEW CONSTRUCTION" in result
    assert "PERMIT" in result