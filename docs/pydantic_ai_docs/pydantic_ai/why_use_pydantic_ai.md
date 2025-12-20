## Why use Pydantic AI

1. **Built by the Pydantic Team**: [Pydantic Validation](https://docs.pydantic.dev/latest/) is the validation layer of the OpenAI SDK, the Google ADK, the Anthropic SDK, LangChain, LlamaIndex, AutoGPT, Transformers, CrewAI, Instructor and many more. _Why use the derivative when you can go straight to the source?_
1. **Model-agnostic**: Supports virtually every [model](models/overview/) and provider: OpenAI, Anthropic, Gemini, DeepSeek, Grok, Cohere, Mistral, and Perplexity; Azure AI Foundry, Amazon Bedrock, Google Vertex AI, Ollama, LiteLLM, Groq, OpenRouter, Together AI, Fireworks AI, Cerebras, Hugging Face, GitHub, Heroku, Vercel, Nebius, OVHcloud, and Outlines. If your favorite model or provider is not listed, you can easily implement a [custom model](models/overview/#custom-models).
1. **Seamless Observability**: Tightly [integrates](logfire/) with [Pydantic Logfire](https://pydantic.dev/logfire), our general-purpose OpenTelemetry observability platform, for real-time debugging, evals-based performance monitoring, and behavior, tracing, and cost tracking. If you already have an observability platform that supports OTel, you can [use that too](logfire/#alternative-observability-backends).
1. **Fully Type-safe**: Designed to give your IDE or AI coding agent as much context as possible for auto-completion and [type checking](agents/#static-type-checking), moving entire classes of errors from runtime to write-time for a bit of that Rust "if it compiles, it works" feel.
1. **Powerful Evals**: Enables you to systematically test and [evaluate](evals/) the performance and accuracy of the agentic systems you build, and monitor the performance over time in Pydantic Logfire.
1. **MCP, A2A, and UI**: Integrates the [Model Context Protocol](mcp/overview/), [Agent2Agent](a2a/), and various [UI event stream](ui/overview/) standards to give your agent access to external tools and data, let it interoperate with other agents, and build interactive applications with streaming event-based communication.
1. **Human-in-the-Loop Tool Approval**: Easily lets you flag that certain tool calls [require approval](deferred-tools/#human-in-the-loop-tool-approval) before they can proceed, possibly depending on tool call arguments, conversation history, or user preferences.
1. **Durable Execution**: Enables you to build [durable agents](durable_execution/overview/) that can preserve their progress across transient API failures and application errors or restarts, and handle long-running, asynchronous, and human-in-the-loop workflows with production-grade reliability.
1. **Streamed Outputs**: Provides the ability to [stream](output/#streamed-results) structured output continuously, with immediate validation, ensuring real time access to generated data.
1. **Graph Support**: Provides a powerful way to define [graphs](graph/) using type hints, for use in complex applications where standard control flow can degrade to spaghetti code.

Realistically though, no list is going to be as convincing as [giving it a try](#next-steps) and seeing how it makes you feel!

**Sign up for our newsletter, _The Pydantic Stack_, with updates & tutorials on Pydantic AI, Logfire, and Pydantic:**

Subscribe
