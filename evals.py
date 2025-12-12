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
    def __init__(self, model_name: str = "claude-haiku-4-5"):
        self.model_name = model_name
        self.anthropic_llm = None

    def load_model(self):
        self.anthropic_llm = ChatAnthropic(
            model=self.model_name,
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


# Create the model instance
model = AnthropicDeepEvalLLM("claude-haiku-4-5")

correct_tool_metric = ToolCorrectnessMetric(model=model)

correctness_metric = GEval(
    model=model,
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

if __name__ == "__main__":
    prompt = "What building code violations have been recorded for 1601 West Chicago Avenue since June 2025? Describe what they were for, and indicate how long they have been open."

    response = agent.invoke({"messages": [{"role": "user", "content": prompt}]})

    # Extract all tools called from the entire conversation
    tools_called = []
    for message in response["messages"]:
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                tools_called.append(ToolCall(name=tool_call["name"]))

    test_case = LLMTestCase(
        input=prompt,
        actual_output=response["messages"][-1].content,
        tools_called=tools_called,
        expected_tools=[
            ToolCall(name="search_address_violations"),
            ToolCall(name="get_violation_details"),
        ],
        expected_output="There are 9 violations recorded at this location on September 8, 2025. They were for structural issues, including exterior repair, interior wall and ceiling issues, fire escape, and more. They have been open since the day they were recorded, for three months and 4 days so far.",
    )

    evaluate(test_cases=[test_case], metrics=[correct_tool_metric, correctness_metric])
