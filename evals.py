# Orchestration for agent

from langchain_anthropic import ChatAnthropic
from main import agent
from deepeval import evaluate
from deepeval.test_case import LLMTestCase, ToolCall
from deepeval.metrics import ToolCorrectnessMetric, GEval
from dotenv import load_dotenv
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCaseParams

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
        # {
        #     "prompt": "What building code violations have been recorded for 1601 West Chicago Avenue since June 2025? Describe what they were for, and indicate how long they have been open.",
        #     "expected_output": "There are 9 violations recorded at this location on September 8, 2025. They were for structural issues, including exterior repair, interior wall and ceiling issues, fire escape, and more. They have been open since the day they were recorded, for more than three months so far.",
        #     "expected_tool_names": [
        #         "search_address_violations",
        #         "get_violation_details",
        #     ],
        # },
        # {
        #     "prompt": "There's a restaurant named Puffy Cakes, I don't know the address. Has that restaurant failed a health inspection since November 1, 2025?",
        #     "expected_output": "Yes, Puffy Cakes has failed at least one health inspection since November 1, 2025.",
        #     "expected_tool_names": [
        #         "search_address_food_inspections",
        #     ],
        # },
        # {
        #     "prompt": "What are the addresses with active building permits within .1 mile of 1601 west chicago ave?",
        #     "expected_output": "1636 W CHICAGO AVE, 1622 W HURON ST, 1512 W HURON ST, 1615 W SUPERIOR ST, 1533 W FRY ST, 1518 W CHICAGO AVE, 1514 W SUPERIOR ST",
        #     "expected_tool_names": [
        #         "geocode_address","get_proximity_to_coords","search_coordinates_active_building_permits"
        #     ],
        # },
        {
            "prompt": "Suggest two restaurants within .25 mile of 1751 West Augusta blvd that have passed their health inspections since November 1, 2025",
            "expected_output": "Koko's Mediterranean Grill and Beatnik & Goodfunk are both possibilities. Puffy Cakes should not be recommended.",
            "expected_tool_names": [
                "geocode_address","get_proximity_to_coords","search_coordinates_food_inspections"
            ],
        },


    ]

    metrics = create_metrics()

    for i in test_cases:
        evaluation = RunTestCase().evaluate(
            i['prompt'], i['expected_output'], i['expected_tool_names']
        )

    # print(evaluation)
