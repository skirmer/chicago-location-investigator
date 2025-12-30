# Chicago Location Investigator Project


This project contains a generative AI agent that assists in research on building codes violations, building permits, and health inspections for food service in Chicago, using the Chicago Open Data Portal. The user submits a plain language query for a particular address, with or without date range filtering, and the agent uses tools to identify the relevant records, and research for further details if appropriate.

The agent has a limited capability to search Chicago Open Data Portal APIs currently, but new functionalities will be added. PRs to add tools for more APIs are welcome, please contribute a function for your favorite dataset about Chicago locations, businesses, and buildings.

### Tips

- For best results, include the cardinal direction (N,S,E,W) and the street type (Blvd, Ave, etc).   
- Dates are not required, although some records go back many years in this dataset. Data will be truncated if too much is returned and your results may be incomplete as a result.  
- You can add filtering language such as "violations currently open" or "permits related to plumbing" etc and the agent will look at the details and inspector notes to try and accommodate.  
- You can also request data from a proximity around the address, such as "All building permits currently active within .5 miles of 123 Main Street". *(The tool will use the OpenStreetMaps geocoder known as Nominatim through geopy to run geocoding, but this will have strict rate limiting, so be careful and DEFINITELY don't send more than 1 request per second. If you just submit a request for a single address, the agent will not need to geocode and will not hit Nominatim.)*


## Example Queries

Here are some examples to help spark your imagination:
* "Recommend five restaurants within 1 mile of [ADDRESS] that have not failed a health department inspection in the past month"
* "I'm walking by the restaurant [NAME OF RESTAURANT] right now - have they failed a health department inspection this year?"
* "Get all the building code violations for addresses from 2025 within .1 mile of [ADDRESS], and check and see if any of those addresses have active building permits. Tell me what the code violations are, and list the building permits so I can see if the permits might be remediating the violations."


## Authentication
In order to run this for yourself, you'll need to have a value in your environment:
* `OPEN_DATA_APP_TOKEN` - a key for accessing the Chicago Open Data Portal API. Learn how you can get yours here for free: https://support.socrata.com/hc/en-us/articles/210138558-Generating-App-Tokens-and-API-Keys

## Models
This project now supports ollama open source models. To set up on MacOS:
```bash 
brew install ollama
ollama pull llama3.1
``` 
(or your choice of tool-capable model)

And don't forget to update the `models/ollama.py` file if you chose something other than llama 3.1.

If you want to use an Anthropic model, update the `models/anthropic.py` file to list the correct model version (it references Claude Haiku 4.5 right now). Then make sure to have your API key in the environment named as `ANTHROPIC_API_KEY`. I like to just use a .env file in the project to manage this sort of thing.

>I find that the llama3.1 model doesn't do as good a job managing tasks and chaining tool calls as claude haiku, but it's a tradeoff with cost that may be worth it.

## To run a query
Install `uv` if you haven't already. Make sure you have the environment variables above set as needed.

```bash
uv run python chicago_location_investigator/main.py --query "Are there any building violations related to electricity at 1600 Chicago Avenue since June 2025?" --model_name "llama3.1"
```
If you don't provide a prompt, one will be provided by default for an example. 

## Testing Framework

There are two testing structures in this repo.  

* The first is unit tests, which check to see that the agent completes some essential tasks (formatting addresses correctly, handling dates) for some basic prompts, and tests all the agent's tools for basic functionality. The unit tests use mocks to divide up the different functionalities and isolate LLM behaviors. Because some of the agent behaviors may not be deterministic, the `test_main` code includes parameterization to let you run these tests multiple times to check for consistent results.

* The second is LLM-as-a-judge evals, using DeepEval. These tests are extremely non-deterministic, and test Correctness (did the agent turn up the correct information), Success (did the question get answered), and Tool Usage (did the agent use the right tools for the job). These evals may need to be refreshed because the data coming out of the API endpoints will change over time, so check the `expected_response` data before running. 

## Notes
The agent does occasionally make mistakes, such as mis-counting the number of records listed, because LLMs are not by nature equipped for arithmetic. I'll be adding tools over time that will assist the agent in doing this kind of calculation so it doesn't try to do it with LLM.

This is not a conversational LLM, just a one-shot agent, so even if the LLM asks follow up questions, there's no mechanism for answering or continuing the exchange. If there's demand for this kind of thing, I may consider adding it later.


