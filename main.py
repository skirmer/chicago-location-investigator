# Orchestration for agent

from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
import os

from tools import search_address_violations, get_violation_details

from dotenv import load_dotenv
import argparse

load_dotenv()
YOUR_APP_TOKEN = os.getenv("YOUR_APP_TOKEN")


model = ChatAnthropic(
    model="claude-haiku-4-5",
)

agent = create_agent(
    model=model,
    tools=[search_address_violations, get_violation_details],
    system_prompt="""You are a research assistant helping users find building code violations in Chicago, Illinois. They will submit an address, and possibly a date or date range to look for.

When addresses are provided, convert them to all-caps and format cardinal directions with one letter (eg, N for North) and abbreviate street types (eg, BLVD for Boulevard).

Available tools:
1. search_address_violations - Get violations for an address with optional date filtering (start_date, end_date, or days parameters)
2. get_violation_details - Get detailed info about a specific violation number

Use multiple tools when helpful to provide comprehensive answers. Do not ask follow up questions or offer to do more.""",
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Query building code violations in Chicago')
    parser.add_argument('--query', type=str, required=False, help='The query to ask about building violations')
    args = parser.parse_args()
    
    if args.query:
        query_text = args.query
    else:
        query_text = "What building code violations have been recorded for 1601 West Chicago Avenue since June 2025? Describe what they were for, and indicate how long they have been open."
        
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

    print("AGENT RESPONSE")
    print(response["messages"][-1].content)
    # for message in response["messages"]:
    #     print(f"\n{message.type.upper()}: {message.content}")
