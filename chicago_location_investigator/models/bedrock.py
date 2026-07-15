from langchain_aws import ChatBedrockConverse

model = ChatBedrockConverse(
    model="us.anthropic.claude-sonnet-5",
    region_name="us-east-1",
)