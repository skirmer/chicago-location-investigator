# Chicago Location Investigator Project


This project contains an agent that assists in research on building codes violations, building permits, and health inspections for food service in Chicago, using the Chicago Open Data Portal. The user submits a plain language query for a particular address, with or without date range filtering, and the agent uses tools to identify the relevant records, and research for further details if appropriate.

For best results, include the cardinal direction (N,S,E,W) and the street type (Blvd, Ave, etc). Dates are not required, although some records go back many years in this dataset. Also, you can add filtering language such as "violations currently open" or "permits related to plumbing" etc and the agent will look at the details and inspector notes to try and accommodate.

## To run a query
Install `uv` if you haven't already. 

```bash
uv run python main.py --query "Are there any building violations related to electricity at 123 Main Street since June 2025?"
```
If you don't provide a prompt, one will be provided by default for an example. 

## Testing Framework

There are two testing structures in this repo.  

* The first is unit tests, which check to see that the agent completes some essential tasks (formatting addresses correctly, handling dates) for some basic prompts. The unit tests use mocks to divide up the different functionalities and isolate LLM behaviors. Because these behaviors may not be deterministic, the code includes parameterization to let you run these tests multiple times to check for consistent results.

* The second is LLM-as-a-judge evals, using DeepEval. There is one eval that tests correct tool calling, and one that checks for accuracy in the response to a test case. 

## Notes
The agent does occasionally make mistakes, such as mis-counting the number of records listed, because LLMs are not by nature equipped for arithmetic. For a production-ready project a separate tool to assist in counting and analysis of the records would be constructed, to prevent the LLM from attempting to do such calculations itself. 

In addition, the API that this agent is using could offer a very wide variety of additional filtering options, but for a small demo such as this I've limited to street address and date.

As background: I recently used this dataset to determine that a gym my friend attends had in fact been inspected and major building violations were found, but that they had not been remedied. This seemed like a nice opportunity to make a tool that would let me check the status of those violations, or check other locations where it seemed like something might be wrong. The code would be easy to adjust to hit the API endpoint for health department violations as well. 

