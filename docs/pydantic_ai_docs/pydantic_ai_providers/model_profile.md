### model_profile

```python
model_profile(model_name: str) -> ModelProfile | None

```

The model profile for the named model, if available.

Source code in `pydantic_ai_slim/pydantic_ai/providers/__init__.py`

```python
def model_profile(self, model_name: str) -> ModelProfile | None:
    """The model profile for the named model, if available."""
    return None  # pragma: no cover

```

Create a new Gateway provider.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `upstream_provider` | `UpstreamProvider | str` | The upstream provider to use. | _required_ | | `route` | `str | None` | The name of the provider or routing group to use to handle the request. If not provided, the default routing group for the API format will be used. | `None` | | `api_key` | `str | None` | The API key to use for authentication. If not provided, the PYDANTIC_AI_GATEWAY_API_KEY environment variable will be used if available. | `None` | | `base_url` | `str | None` | The base URL to use for the Gateway. If not provided, the PYDANTIC_AI_GATEWAY_BASE_URL environment variable will be used if available. Otherwise, defaults to https://gateway.pydantic.dev/proxy. | `None` | | `http_client` | `AsyncClient | None` | The HTTP client to use for the Gateway. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/providers/gateway.py`

```python
def gateway_provider(
    upstream_provider: UpstreamProvider | str,
    /,
    *,
    # Every provider
    route: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    # OpenAI, Groq, Anthropic & Gemini - Only Bedrock doesn't have an HTTPX client.
    http_client: httpx.AsyncClient | None = None,
) -> Provider[Any]:
    """Create a new Gateway provider.

    Args:
        upstream_provider: The upstream provider to use.
        route: The name of the provider or routing group to use to handle the request. If not provided, the default
            routing group for the API format will be used.
        api_key: The API key to use for authentication. If not provided, the `PYDANTIC_AI_GATEWAY_API_KEY`
            environment variable will be used if available.
        base_url: The base URL to use for the Gateway. If not provided, the `PYDANTIC_AI_GATEWAY_BASE_URL`
            environment variable will be used if available. Otherwise, defaults to `https://gateway.pydantic.dev/proxy`.
        http_client: The HTTP client to use for the Gateway.
    """
    api_key = api_key or os.getenv('PYDANTIC_AI_GATEWAY_API_KEY', os.getenv('PAIG_API_KEY'))
    if not api_key:
        raise UserError(
            'Set the `PYDANTIC_AI_GATEWAY_API_KEY` environment variable or pass it via `gateway_provider(..., api_key=...)`'
            ' to use the Pydantic AI Gateway provider.'
        )

    base_url = base_url or os.getenv('PYDANTIC_AI_GATEWAY_BASE_URL', os.getenv('PAIG_BASE_URL', GATEWAY_BASE_URL))
    http_client = http_client or cached_async_http_client(provider=f'gateway/{upstream_provider}')
    http_client.event_hooks = {'request': [_request_hook(api_key)]}

    if route is None:
        # Use the implied providerId as the default route.
        route = normalize_gateway_provider(upstream_provider)

    base_url = _merge_url_path(base_url, route)

    if upstream_provider in ('openai', 'openai-chat', 'openai-responses', 'chat', 'responses'):
        from .openai import OpenAIProvider

        return OpenAIProvider(api_key=api_key, base_url=base_url, http_client=http_client)
    elif upstream_provider == 'groq':
        from .groq import GroqProvider

        return GroqProvider(api_key=api_key, base_url=base_url, http_client=http_client)
    elif upstream_provider == 'anthropic':
        from anthropic import AsyncAnthropic

        from .anthropic import AnthropicProvider

        return AnthropicProvider(
            anthropic_client=AsyncAnthropic(auth_token=api_key, base_url=base_url, http_client=http_client)
        )
    elif upstream_provider in ('bedrock', 'converse'):
        from .bedrock import BedrockProvider

        return BedrockProvider(
            api_key=api_key,
            base_url=base_url,
            region_name='pydantic-ai-gateway',  # Fake region name to avoid NoRegionError
        )
    elif upstream_provider in ('google-vertex', 'gemini'):
        from .google import GoogleProvider

        return GoogleProvider(vertexai=True, api_key=api_key, base_url=base_url, http_client=http_client)
    else:
        raise UserError(f'Unknown upstream provider: {upstream_provider}')

```
