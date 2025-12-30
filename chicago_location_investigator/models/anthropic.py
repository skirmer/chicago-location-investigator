from langchain_anthropic import ChatAnthropic


model = ChatAnthropic(
    temperature=0,
    model="claude-haiku-4-5",
)
