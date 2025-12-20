## Slim Install

If you know which model you're going to use and want to avoid installing superfluous packages, you can use the [`pydantic-ai-slim`](https://pypi.org/project/pydantic-ai-slim/) package. For example, if you're using just OpenAIChatModel, you would run:

```bash
pip install "pydantic-ai-slim[openai]"

```

```bash
uv add "pydantic-ai-slim[openai]"

```

`pydantic-ai-slim` has the following optional groups:

- `logfire` â€” installs [Pydantic Logfire](../logfire/) dependency `logfire` [PyPI â†—](https://pypi.org/project/logfire)
- `evals` â€” installs [Pydantic Evals](../evals/) dependency `pydantic-evals` [PyPI â†—](https://pypi.org/project/pydantic-evals)
- `openai` â€” installs [OpenAI Model](../models/openai/) dependency `openai` [PyPI â†—](https://pypi.org/project/openai)
- `vertexai` â€” installs `GoogleVertexProvider` dependencies `google-auth` [PyPI â†—](https://pypi.org/project/google-auth) and `requests` [PyPI â†—](https://pypi.org/project/requests)
- `google` â€” installs [Google Model](../models/google/) dependency `google-genai` [PyPI â†—](https://pypi.org/project/google-genai)
- `anthropic` â€” installs [Anthropic Model](../models/anthropic/) dependency `anthropic` [PyPI â†—](https://pypi.org/project/anthropic)
- `groq` â€” installs [Groq Model](../models/groq/) dependency `groq` [PyPI â†—](https://pypi.org/project/groq)
- `mistral` â€” installs [Mistral Model](../models/mistral/) dependency `mistralai` [PyPI â†—](https://pypi.org/project/mistralai)
- `cohere` - installs [Cohere Model](../models/cohere/) dependency `cohere` [PyPI â†—](https://pypi.org/project/cohere)
- `bedrock` - installs [Bedrock Model](../models/bedrock/) dependency `boto3` [PyPI â†—](https://pypi.org/project/boto3)
- `huggingface` - installs [Hugging Face Model](../models/huggingface/) dependency `huggingface-hub[inference]` [PyPI â†—](https://pypi.org/project/huggingface-hub)
- `outlines-transformers` - installs [Outlines Model](../models/outlines/) dependency `outlines[transformers]` [PyPI â†—](https://pypi.org/project/outlines)
- `outlines-llamacpp` - installs [Outlines Model](../models/outlines/) dependency `outlines[llamacpp]` [PyPI â†—](https://pypi.org/project/outlines)
- `outlines-mlxlm` - installs [Outlines Model](../models/outlines/) dependency `outlines[mlxlm]` [PyPI â†—](https://pypi.org/project/outlines)
- `outlines-sglang` - installs [Outlines Model](../models/outlines/) dependency `outlines[sglang]` [PyPI â†—](https://pypi.org/project/outlines)
- `outlines-vllm-offline` - installs [Outlines Model](../models/outlines/) dependencies `outlines` [PyPI â†—](https://pypi.org/project/outlines) and `vllm` [PyPI â†—](https://pypi.org/project/vllm)
- `duckduckgo` - installs [DuckDuckGo Search Tool](../common-tools/#duckduckgo-search-tool) dependency `ddgs` [PyPI â†—](https://pypi.org/project/ddgs)
- `tavily` - installs [Tavily Search Tool](../common-tools/#tavily-search-tool) dependency `tavily-python` [PyPI â†—](https://pypi.org/project/tavily-python)
- `cli` - installs [CLI](../cli/) dependencies `rich` [PyPI â†—](https://pypi.org/project/rich), `prompt-toolkit` [PyPI â†—](https://pypi.org/project/prompt-toolkit), and `argcomplete` [PyPI â†—](https://pypi.org/project/argcomplete)
- `mcp` - installs [MCP](../mcp/client/) dependency `mcp` [PyPI â†—](https://pypi.org/project/mcp)
- `fastmcp` - installs [FastMCP](../mcp/fastmcp-client/) dependency `fastmcp` [PyPI â†—](https://pypi.org/project/fastmcp)
- `a2a` - installs [A2A](../a2a/) dependency `fasta2a` [PyPI â†—](https://pypi.org/project/fasta2a)
- `ui` - installs [UI Event Streams](../ui/overview/) dependency `starlette` [PyPI â†—](https://pypi.org/project/starlette)
- `ag-ui` - installs [AG-UI Event Stream Protocol](../ui/ag-ui/) dependencies `ag-ui-protocol` [PyPI â†—](https://pypi.org/project/ag-ui-protocol) and `starlette` [PyPI â†—](https://pypi.org/project/starlette)
- `dbos` - installs [DBOS Durable Execution](../durable_execution/dbos/) dependency `dbos` [PyPI â†—](https://pypi.org/project/dbos)
- `prefect` - installs [Prefect Durable Execution](../durable_execution/prefect/) dependency `prefect` [PyPI â†—](https://pypi.org/project/prefect)

You can also install dependencies for multiple models and use cases, for example:

```bash
pip install "pydantic-ai-slim[openai,google,logfire]"

```

```bash
uv add "pydantic-ai-slim[openai,google,logfire]"

```
