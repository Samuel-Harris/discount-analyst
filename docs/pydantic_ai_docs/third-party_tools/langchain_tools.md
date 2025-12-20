## LangChain Tools

If you'd like to use a tool from LangChain's [community tool library](https://python.langchain.com/docs/integrations/tools/) with Pydantic AI, you can use the tool_from_langchain convenience method. Note that Pydantic AI will not validate the arguments in this case -- it's up to the model to provide arguments matching the schema specified by the LangChain tool, and up to the LangChain tool to raise an error if the arguments are invalid.

You will need to install the `langchain-community` package and any others required by the tool in question.

Here is how you can use the LangChain `DuckDuckGoSearchRun` tool, which requires the `ddgs` package:

```python
from langchain_community.tools import DuckDuckGoSearchRun

from pydantic_ai import Agent
from pydantic_ai.ext.langchain import tool_from_langchain

search = DuckDuckGoSearchRun()
search_tool = tool_from_langchain(search)

agent = Agent(
    'google-gla:gemini-2.5-flash',
    tools=[search_tool],
)

result = agent.run_sync('What is the release date of Elden Ring Nightreign?')  # (1)!
print(result.output)
#> Elden Ring Nightreign is planned to be released on May 30, 2025.

```

1. The release date of this game is the 30th of May 2025, which is after the knowledge cutoff for Gemini 2.0 (August 2024).

If you'd like to use multiple LangChain tools or a LangChain [toolkit](https://python.langchain.com/docs/concepts/tools/#toolkits), you can use the LangChainToolset [toolset](../toolsets/) which takes a list of LangChain tools:

[Learn about Gateway](../gateway)

```python
from langchain_community.agent_toolkits import SlackToolkit

from pydantic_ai import Agent
from pydantic_ai.ext.langchain import LangChainToolset

toolkit = SlackToolkit()
toolset = LangChainToolset(toolkit.get_tools())

agent = Agent('gateway/openai:gpt-5', toolsets=[toolset])
