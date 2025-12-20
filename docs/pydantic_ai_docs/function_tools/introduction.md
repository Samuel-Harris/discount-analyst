Function tools provide a mechanism for models to perform actions and retrieve extra information to help them generate a response.

They're useful when you want to enable the model to take some action and use the result, when it is impractical or impossible to put all the context an agent might need into the instructions, or when you want to make agents' behavior more deterministic or reliable by deferring some of the logic required to generate a response to another (not necessarily AI-powered) tool.

If you want a model to be able to call a function as its final action, without the result being sent back to the model, you can use an [output function](../output/#output-functions) instead.

There are a number of ways to register tools with an agent:

- via the @agent.tool decorator â€” for tools that need access to the agent context
- via the @agent.tool_plain decorator â€” for tools that do not need access to the agent context
- via the tools keyword argument to `Agent` which can take either plain functions, or instances of Tool

For more advanced use cases, the [toolsets](../toolsets/) feature lets you manage collections of tools (built by you or provided by an [MCP server](../mcp/client/) or other [third party](../third-party-tools/#third-party-tools)) and register them with an agent in one go via the toolsets keyword argument to `Agent`. Internally, all `tools` and `toolsets` are gathered into a single [combined toolset](../toolsets/#combining-toolsets) that's made available to the model.

Function tools vs. RAG

Function tools are basically the "R" of RAG (Retrieval-Augmented Generation) â€” they augment what the model can do by letting it request extra information.

The main semantic difference between Pydantic AI Tools and RAG is RAG is synonymous with vector search, while Pydantic AI tools are more general-purpose. (Note: we may add support for vector search functionality in the future, particularly an API for generating embeddings. See [#58](https://github.com/pydantic/pydantic-ai/issues/58))

Function Tools vs. Structured Outputs

As the name suggests, function tools use the model's "tools" or "functions" API to let the model know what is available to call. Tools or functions are also used to define the schema(s) for [structured output](../output/) when using the default [tool output mode](../output/#tool-output), thus a model might have access to many tools, some of which call function tools while others end the run and produce a final output.
