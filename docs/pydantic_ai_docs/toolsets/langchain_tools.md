### LangChain Tools

If you'd like to use tools or a [toolkit](https://python.langchain.com/docs/concepts/tools/#toolkits) from LangChain's [community tool library](https://python.langchain.com/docs/integrations/tools/) with Pydantic AI, you can use the LangChainToolset which takes a list of LangChain tools. Note that Pydantic AI will not validate the arguments in this case -- it's up to the model to provide arguments matching the schema specified by the LangChain tool, and up to the LangChain tool to raise an error if the arguments are invalid.

You will need to install the `langchain-community` package and any others required by the tools in question.

[Learn about Gateway](../gateway)

```python
from langchain_community.agent_toolkits import SlackToolkit

from pydantic_ai import Agent
from pydantic_ai.ext.langchain import LangChainToolset

toolkit = SlackToolkit()
toolset = LangChainToolset(toolkit.get_tools())

agent = Agent('gateway/openai:gpt-5', toolsets=[toolset])
