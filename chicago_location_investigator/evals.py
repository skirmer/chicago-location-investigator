# Orchestration for agent

from langchain_anthropic import ChatAnthropic
from main import agent
from deepeval import evaluate
from deepeval.test_case import LLMTestCase, ToolCall
from deepeval.metrics import ToolCorrectnessMetric, GEval
from dotenv import load_dotenv
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCaseParams
from main import model

from tools.tools_geocoding import get_proximity_to_coords

from tools.tools_violations import search_address_violations, get_violation_details, search_coordinates_violations

from tools.tools_permits import search_address_active_building_permits, search_coordinates_active_building_permits

from tools.tools_food import search_address_food_inspections, search_coordinates_food_inspections
from langchain.agents import create_agent
import json
from datetime import datetime


load_dotenv()


class AnthropicDeepEvalLLM(DeepEvalBaseLLM):
    def __init__(self, model_name: str = "claude-haiku-4-5", temperature: int = 0):
        self.model_name = model_name
        self.anthropic_llm = None
        self.temperature = temperature

    def load_model(self):
        self.anthropic_llm = ChatAnthropic(
            model=self.model_name, temperature=self.temperature
        )
        return self.anthropic_llm

    def generate(self, prompt: str) -> str:
        if self.anthropic_llm is None:
            self.load_model()
        response = self.anthropic_llm.invoke(prompt)
        return response.text

    async def a_generate(self, prompt: str) -> str:
        if self.anthropic_llm is None:
            self.load_model()
        response = await self.anthropic_llm.ainvoke(prompt)
        return response.text

    def get_model_name(self) -> str:
        return self.model_name


def create_model():
    return AnthropicDeepEvalLLM("claude-haiku-4-5", temperature=0)

def mock_geocode_address(address:str):
    """Provide an address including city and state, and this function will return geocoordinates for this location.
    This is rate limited as the geocoding API is free, so don't send more than 1 request per second.

    Args: 
        address: The building address in all-caps format (e.g., '1601 W CHICAGO AVE') - unless otherwise indicated, use "CHICAGO, ILLINOIS" as the city and state.

    Returns: 
        Latitude, Longitude as tuple
    """    
    print(address)


    if '1601 W CHICAGO AVE' in address:
        return (41.8958, -87.6688)
    elif '1751 W AUGUSTA BLVD' in address:
        return (41.8991, -87.6721)
    elif '2951 W ARMITAGE AVE' in address:
        return (41.917289, -87.701174)
    else:
        return (41.8781, -87.6298)


agent = create_agent(
    model=model,
    tools=[search_address_violations, get_violation_details, search_address_active_building_permits, search_address_food_inspections, mock_geocode_address, get_proximity_to_coords, search_coordinates_violations, search_coordinates_active_building_permits, search_coordinates_food_inspections],
    system_prompt="""You are a research assistant helping users find information about buildings in Chicago, Illinois. They will submit an address, and possibly a date or date range to look for.

When addresses are provided, convert them to all-caps and format cardinal directions with one letter (eg, N for North) and abbreviate street types (eg, BLVD for Boulevard). Where restaurant names are provided, also convert them to all-caps before passing to a tool.

Available tools:
1. mock_geocode_address - If the question involves looking around the vicinity of an address, geocode that address to get coordinates.
2. get_proximity_to_coords - This function takes in coordinates of an address and calculates the north, south, east, and west bounds for the requested radius. Radius must be provided in miles.
3. search_address_violations - Get building code violations for an address with optional date filtering (start_date, end_date, or days parameters)
4. get_violation_details - Get detailed info about a specific building code violation number
5. search_address_active_building_permits - Get a listing of any active building permits for an address.
6. search_coordinates_active_building_permits - Get a listing of any active building permits found within coordinate boundaries.
7. search_address_food_inspections - Get a listing of health department inspections for restaurants or food services. Accepts name and/or address.
8. search_coordinates_food_inspections - Get a listing of health department inspections for restaurants or food services found within coordinate boundaries.

Use multiple tools when helpful to provide comprehensive answers. Do not ask follow up questions or offer to do more. If results had to be truncated due to length, let the user know.""",
)



def create_metrics():
    correct_tool_metric = ToolCorrectnessMetric(model=create_model())

    correctness_metric = GEval(
        model=create_model(),
        name="Correctness",
        evaluation_steps=[
            "Check whether the facts in 'actual output' contradicts any facts in 'expected output'",
        ],
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
    )

    success_metric = GEval(
        model=create_model(),
        name="Success",
        evaluation_steps=[
            "Check whether the response successfully answers the question that was asked.",
        ],
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
    )

    return [correctness_metric, correct_tool_metric, success_metric]


class RunTestCase:
    def __init__(self):
        self.prompt = None
        self.tools_called = None
        self.response = None

    def get_called_tools(self):
        tools_called = []
        for message in self.response["messages"]:
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    tools_called.append(ToolCall(name=tool_call["name"]))
        self.tools_called = tools_called

    def create_test_case(self, expected_output, expected_tool_names):

        expected_tool_list = [ToolCall(name=x) for x in expected_tool_names]

        return LLMTestCase(
            input=self.prompt,
            actual_output=self.response["messages"][-1].content,
            tools_called=self.tools_called,
            expected_tools=expected_tool_list,
            expected_output=expected_output,
        )

    def run_prompt(self, prompt):
        self.prompt = prompt
        self.response = agent.invoke(
            {"messages": [{"role": "user", "content": self.prompt}]}
        )

    def evaluate(self, prompt, expected_output, expected_tool_names):
        self.run_prompt(prompt)
        self.get_called_tools()

        test_case = self.create_test_case(expected_output, expected_tool_names)

        return evaluate(test_cases=[test_case], metrics=metrics)


if __name__ == "__main__":
    test_cases = [
        # Test two-step on just building codes
        {
            "prompt": "What building code violations have been recorded for 1601 West Chicago Avenue since June 2025? Describe what they were for, and indicate how long they have been open.",
            "expected_output": "There are 9 violations recorded at this location on September 8, 2025. They were for structural issues, including exterior repair, interior wall and ceiling issues, fire escape, and more. They have been open since the day they were recorded, for more than three months so far.",
            "expected_tool_names": [
                "search_address_violations",
                "get_violation_details",
            ],
        },
        # Test single step on food
        {
            "prompt": "There's a restaurant named Puffy Cakes, I don't know the address. Has that restaurant failed a health inspection since November 1, 2025?",
            "expected_output": "Yes, Puffy Cakes has failed at least one health inspection since November 1, 2025.",
            "expected_tool_names": [
                "search_address_food_inspections",
            ],
        },
        # Test multi step with geocoding and building permits
        {
            "prompt": "What are the addresses with active building permits within .1 mile of 1601 west chicago ave?",
            "expected_output": "1636 W CHICAGO AVE, 1622 W HURON ST, 1512 W HURON ST, 1615 W SUPERIOR ST, 1533 W FRY ST, 1518 W CHICAGO AVE, 1514 W SUPERIOR ST",
            "expected_tool_names": [
                "mock_geocode_address","get_proximity_to_coords","search_coordinates_active_building_permits"
            ],
        },
        # Test restaurants multi step with geocoding and deeper logic
        {
            "prompt": "Suggest 2 restaurants within .25 mile of 2951 W armitage ave that have passed all of their health inspections since October 1, 2025",
            "expected_output": "The Spice Room, Gretel, Papa John's, Bang Bang, and Buffalo Wild Wings are suitable recommendations, but the answer should select two from this list. Dante's and Parson's Chicken and Fish should not be recommended.",
            "expected_tool_names": [
                "mock_geocode_address",
                "get_proximity_to_coords",
                "search_coordinates_food_inspections",
            ],
        },
        # Test multi step geocoding with building permits and violations combined logic
        {
            "prompt": "Find all the building code violations from 2025 within .1 mile of 2951 W armitage ave.Check and see if any of the addresses have active building permits. Tell me what the violations are, and list the building permits so I can see if the permits might be remediating the violations.",
            "expected_output": "1918 N FRANCISCO AVE, 1926 N HUMBOLDT BLVD, 1930 N HUMBOLDT BLVD, 3013 W ARMITAGE AVE, 3004 W ARMITAGE AVE, 1908 N FRANCISCO AVE, and 3007 W ARMITAGE AVE have open building code violations, and there are several building permits in the area. Of these, there are building permits for 1908 N FRANCISCO AVE, 1918 N FRANCISCO AVE, and 3007 W ARMITAGE AVE. Some permits for 1918 N FRANCISCO, 1926 N HUMBOLDT BLVD, and 3007 W ARMITAGE seem like they might be remediating the building code violations, but 1908 N FRANCISCO is building something new.",
            "expected_tool_names": [
                "mock_geocode_address",
                "get_proximity_to_coords",
                "search_coordinates_active_building_permits",
                "search_coordinates_violations"
            ],
        },
    ]

    metrics = create_metrics()

    for i in test_cases:
        evaluation = RunTestCase().evaluate(
            i["prompt"], i["expected_output"], i["expected_tool_names"]
        )
        
        # Generate timestamp and create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/test_result{timestamp}.json"
        
        # Collect results for each test case
        test_result = {
            "timestamp": timestamp,
            "prompt": i["prompt"],
            "expected_output": i["expected_output"],
            "expected_tool_names": i["expected_tool_names"],
            "metrics": []
        }
        
        # Extract metric results
        for test_case in evaluation.test_results:
            for metric_result in test_case.metrics_data:
                test_result["metrics"].append({
                    "name": metric_result.name,
                    "score": metric_result.score,
                    "success": metric_result.success,
                    "reason": metric_result.reason if hasattr(metric_result, 'reason') else None
                })
                
        # Write evaluation results to file
        with open(filename, 'w') as f:
            json.dump(test_result, f, indent=2, default=str)

        print(f"Results written to {filename}")

