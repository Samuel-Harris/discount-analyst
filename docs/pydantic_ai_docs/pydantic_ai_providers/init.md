### **init**

```python
__init__(
    *,
    api_key: str | None = None,
    api_base: str | None = None
) -> None

```

```python
__init__(
    *,
    api_key: str | None = None,
    api_base: str | None = None,
    http_client: AsyncClient
) -> None

```

```python
__init__(*, openai_client: AsyncOpenAI) -> None

```

```python
__init__(
    *,
    api_key: str | None = None,
    api_base: str | None = None,
    openai_client: AsyncOpenAI | None = None,
    http_client: AsyncClient | None = None
) -> None

```

Initialize a LiteLLM provider.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `api_key` | `str | None` | API key for the model provider. If None, LiteLLM will try to get it from environment variables. | `None` | | `api_base` | `str | None` | Base URL for the model provider. Use this for custom endpoints or self-hosted models. | `None` | | `openai_client` | `AsyncOpenAI | None` | Pre-configured OpenAI client. If provided, other parameters are ignored. | `None` | | `http_client` | `AsyncClient | None` | Custom HTTP client to use. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/providers/litellm.py`

```python
def __init__(
    self,
    *,
    api_key: str | None = None,
    api_base: str | None = None,
    openai_client: AsyncOpenAI | None = None,
    http_client: AsyncHTTPClient | None = None,
) -> None:
    """Initialize a LiteLLM provider.

    Args:
        api_key: API key for the model provider. If None, LiteLLM will try to get it from environment variables.
        api_base: Base URL for the model provider. Use this for custom endpoints or self-hosted models.
        openai_client: Pre-configured OpenAI client. If provided, other parameters are ignored.
        http_client: Custom HTTP client to use.
    """
    if openai_client is not None:
        self._client = openai_client
        return

    # Create OpenAI client that will be used with LiteLLM's completion function
    # The actual API calls will be intercepted and routed through LiteLLM
    if http_client is not None:
        self._client = AsyncOpenAI(
            base_url=api_base, api_key=api_key or 'litellm-placeholder', http_client=http_client
        )
    else:
        http_client = cached_async_http_client(provider='litellm')
        self._client = AsyncOpenAI(
            base_url=api_base, api_key=api_key or 'litellm-placeholder', http_client=http_client
        )

```

Bases: `Provider[AsyncOpenAI]`

Provider for Nebius AI Studio API.

Source code in `pydantic_ai_slim/pydantic_ai/providers/nebius.py`

```python
class NebiusProvider(Provider[AsyncOpenAI]):
    """Provider for Nebius AI Studio API."""

    @property
    def name(self) -> str:
        return 'nebius'

    @property
    def base_url(self) -> str:
        return 'https://api.studio.nebius.com/v1'

    @property
    def client(self) -> AsyncOpenAI:
        return self._client

    def model_profile(self, model_name: str) -> ModelProfile | None:
        provider_to_profile = {
            'meta-llama': meta_model_profile,
            'deepseek-ai': deepseek_model_profile,
            'qwen': qwen_model_profile,
            'google': google_model_profile,
            'openai': harmony_model_profile,  # used for gpt-oss models on Nebius
            'mistralai': mistral_model_profile,
            'moonshotai': moonshotai_model_profile,
        }

        profile = None

        try:
            model_name = model_name.lower()
            provider, model_name = model_name.split('/', 1)
        except ValueError:
            raise UserError(f"Model name must be in 'provider/model' format, got: {model_name!r}")
        if provider in provider_to_profile:
            profile = provider_to_profile[provider](model_name)

        # As NebiusProvider is always used with OpenAIChatModel, which used to unconditionally use OpenAIJsonSchemaTransformer,
        # we need to maintain that behavior unless json_schema_transformer is set explicitly
        return OpenAIModelProfile(json_schema_transformer=OpenAIJsonSchemaTransformer).update(profile)

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, *, api_key: str) -> None: ...

    @overload
    def __init__(self, *, api_key: str, http_client: httpx.AsyncClient) -> None: ...

    @overload
    def __init__(self, *, openai_client: AsyncOpenAI | None = None) -> None: ...

    def __init__(
        self,
        *,
        api_key: str | None = None,
        openai_client: AsyncOpenAI | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        api_key = api_key or os.getenv('NEBIUS_API_KEY')
        if not api_key and openai_client is None:
            raise UserError(
                'Set the `NEBIUS_API_KEY` environment variable or pass it via '
                '`NebiusProvider(api_key=...)` to use the Nebius AI Studio provider.'
            )

        if openai_client is not None:
            self._client = openai_client
        elif http_client is not None:
            self._client = AsyncOpenAI(base_url=self.base_url, api_key=api_key, http_client=http_client)
        else:
            http_client = cached_async_http_client(provider='nebius')
            self._client = AsyncOpenAI(base_url=self.base_url, api_key=api_key, http_client=http_client)

```

Bases: `Provider[AsyncOpenAI]`

Provider for OVHcloud AI Endpoints.

Source code in `pydantic_ai_slim/pydantic_ai/providers/ovhcloud.py`

```python
class OVHcloudProvider(Provider[AsyncOpenAI]):
    """Provider for OVHcloud AI Endpoints."""

    @property
    def name(self) -> str:
        return 'ovhcloud'

    @property
    def base_url(self) -> str:
        return 'https://oai.endpoints.kepler.ai.cloud.ovh.net/v1'

    @property
    def client(self) -> AsyncOpenAI:
        return self._client

    def model_profile(self, model_name: str) -> ModelProfile | None:
        model_name = model_name.lower()

        prefix_to_profile = {
            'llama': meta_model_profile,
            'meta-': meta_model_profile,
            'deepseek': deepseek_model_profile,
            'mistral': mistral_model_profile,
            'gpt': harmony_model_profile,
            'qwen': qwen_model_profile,
        }

        profile = None
        for prefix, profile_func in prefix_to_profile.items():
            if model_name.startswith(prefix):
                profile = profile_func(model_name)

        # As the OVHcloud AI Endpoints API is OpenAI-compatible, let's assume we also need OpenAIJsonSchemaTransformer.
        return OpenAIModelProfile(json_schema_transformer=OpenAIJsonSchemaTransformer).update(profile)

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, *, api_key: str) -> None: ...

    @overload
    def __init__(self, *, api_key: str, http_client: httpx.AsyncClient) -> None: ...

    @overload
    def __init__(self, *, openai_client: AsyncOpenAI | None = None) -> None: ...

    def __init__(
        self,
        *,
        api_key: str | None = None,
        openai_client: AsyncOpenAI | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        api_key = api_key or os.getenv('OVHCLOUD_API_KEY')
        if not api_key and openai_client is None:
            raise UserError(
                'Set the `OVHCLOUD_API_KEY` environment variable or pass it via '
                '`OVHcloudProvider(api_key=...)` to use OVHcloud AI Endpoints provider.'
            )

        if openai_client is not None:
            self._client = openai_client
        elif http_client is not None:
            self._client = AsyncOpenAI(base_url=self.base_url, api_key=api_key, http_client=http_client)
        else:
            http_client = cached_async_http_client(provider='ovhcloud')
            self._client = AsyncOpenAI(base_url=self.base_url, api_key=api_key, http_client=http_client)

```
