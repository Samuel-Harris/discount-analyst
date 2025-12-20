### CohereProvider

Bases: `Provider[AsyncClientV2]`

Provider for Cohere API.

Source code in `pydantic_ai_slim/pydantic_ai/providers/cohere.py`

```python
class CohereProvider(Provider[AsyncClientV2]):
    """Provider for Cohere API."""

    @property
    def name(self) -> str:
        return 'cohere'

    @property
    def base_url(self) -> str:
        client_wrapper = self.client._client_wrapper  # type: ignore
        return str(client_wrapper.get_base_url())

    @property
    def client(self) -> AsyncClientV2:
        return self._client

    def model_profile(self, model_name: str) -> ModelProfile | None:
        return cohere_model_profile(model_name)

    def __init__(
        self,
        *,
        api_key: str | None = None,
        cohere_client: AsyncClientV2 | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Create a new Cohere provider.

        Args:
            api_key: The API key to use for authentication, if not provided, the `CO_API_KEY` environment variable
                will be used if available.
            cohere_client: An existing
                [AsyncClientV2](https://github.com/cohere-ai/cohere-python)
                client to use. If provided, `api_key` and `http_client` must be `None`.
            http_client: An existing `httpx.AsyncClient` to use for making HTTP requests.
        """
        if cohere_client is not None:
            assert http_client is None, 'Cannot provide both `cohere_client` and `http_client`'
            assert api_key is None, 'Cannot provide both `cohere_client` and `api_key`'
            self._client = cohere_client
        else:
            api_key = api_key or os.getenv('CO_API_KEY')
            if not api_key:
                raise UserError(
                    'Set the `CO_API_KEY` environment variable or pass it via `CohereProvider(api_key=...)`'
                    'to use the Cohere provider.'
                )

            base_url = os.getenv('CO_BASE_URL')
            if http_client is not None:
                self._client = AsyncClientV2(api_key=api_key, httpx_client=http_client, base_url=base_url)
            else:
                http_client = cached_async_http_client(provider='cohere')
                self._client = AsyncClientV2(api_key=api_key, httpx_client=http_client, base_url=base_url)

```

#### **init**

```python
__init__(
    *,
    api_key: str | None = None,
    cohere_client: AsyncClientV2 | None = None,
    http_client: AsyncClient | None = None
) -> None

```

Create a new Cohere provider.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `api_key` | `str | None` | The API key to use for authentication, if not provided, the CO_API_KEY environment variable will be used if available. | `None` | | `cohere_client` | `AsyncClientV2 | None` | An existing AsyncClientV2 client to use. If provided, api_key and http_client must be None. | `None` | | `http_client` | `AsyncClient | None` | An existing httpx.AsyncClient to use for making HTTP requests. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/providers/cohere.py`

```python
def __init__(
    self,
    *,
    api_key: str | None = None,
    cohere_client: AsyncClientV2 | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> None:
    """Create a new Cohere provider.

    Args:
        api_key: The API key to use for authentication, if not provided, the `CO_API_KEY` environment variable
            will be used if available.
        cohere_client: An existing
            [AsyncClientV2](https://github.com/cohere-ai/cohere-python)
            client to use. If provided, `api_key` and `http_client` must be `None`.
        http_client: An existing `httpx.AsyncClient` to use for making HTTP requests.
    """
    if cohere_client is not None:
        assert http_client is None, 'Cannot provide both `cohere_client` and `http_client`'
        assert api_key is None, 'Cannot provide both `cohere_client` and `api_key`'
        self._client = cohere_client
    else:
        api_key = api_key or os.getenv('CO_API_KEY')
        if not api_key:
            raise UserError(
                'Set the `CO_API_KEY` environment variable or pass it via `CohereProvider(api_key=...)`'
                'to use the Cohere provider.'
            )

        base_url = os.getenv('CO_BASE_URL')
        if http_client is not None:
            self._client = AsyncClientV2(api_key=api_key, httpx_client=http_client, base_url=base_url)
        else:
            http_client = cached_async_http_client(provider='cohere')
            self._client = AsyncClientV2(api_key=api_key, httpx_client=http_client, base_url=base_url)

```

Bases: `Provider[AsyncOpenAI]`

Provider for Cerebras API.

Source code in `pydantic_ai_slim/pydantic_ai/providers/cerebras.py`

```python
class CerebrasProvider(Provider[AsyncOpenAI]):
    """Provider for Cerebras API."""

    @property
    def name(self) -> str:
        return 'cerebras'

    @property
    def base_url(self) -> str:
        return 'https://api.cerebras.ai/v1'

    @property
    def client(self) -> AsyncOpenAI:
        return self._client

    def model_profile(self, model_name: str) -> ModelProfile | None:
        prefix_to_profile = {'llama': meta_model_profile, 'qwen': qwen_model_profile, 'gpt-oss': harmony_model_profile}

        profile = None
        for prefix, profile_func in prefix_to_profile.items():
            model_name = model_name.lower()
            if model_name.startswith(prefix):
                profile = profile_func(model_name)

        # According to https://inference-docs.cerebras.ai/resources/openai#currently-unsupported-openai-features,
        # Cerebras doesn't support some model settings.
        unsupported_model_settings = (
            'frequency_penalty',
            'logit_bias',
            'presence_penalty',
            'parallel_tool_calls',
            'service_tier',
        )
        return OpenAIModelProfile(
            json_schema_transformer=OpenAIJsonSchemaTransformer,
            openai_unsupported_model_settings=unsupported_model_settings,
        ).update(profile)

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
        api_key = api_key or os.getenv('CEREBRAS_API_KEY')
        if not api_key and openai_client is None:
            raise UserError(
                'Set the `CEREBRAS_API_KEY` environment variable or pass it via `CerebrasProvider(api_key=...)` '
                'to use the Cerebras provider.'
            )

        if openai_client is not None:
            self._client = openai_client
        elif http_client is not None:
            self._client = AsyncOpenAI(base_url=self.base_url, api_key=api_key, http_client=http_client)
        else:
            http_client = cached_async_http_client(provider='cerebras')
            self._client = AsyncOpenAI(base_url=self.base_url, api_key=api_key, http_client=http_client)

```

Bases: `Provider[Mistral]`

Provider for Mistral API.

Source code in `pydantic_ai_slim/pydantic_ai/providers/mistral.py`

```python
class MistralProvider(Provider[Mistral]):
    """Provider for Mistral API."""

    @property
    def name(self) -> str:
        return 'mistral'

    @property
    def base_url(self) -> str:
        return self.client.sdk_configuration.get_server_details()[0]

    @property
    def client(self) -> Mistral:
        return self._client

    def model_profile(self, model_name: str) -> ModelProfile | None:
        return mistral_model_profile(model_name)

    @overload
    def __init__(self, *, mistral_client: Mistral | None = None) -> None: ...

    @overload
    def __init__(self, *, api_key: str | None = None, http_client: httpx.AsyncClient | None = None) -> None: ...

    def __init__(
        self,
        *,
        api_key: str | None = None,
        mistral_client: Mistral | None = None,
        base_url: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Create a new Mistral provider.

        Args:
            api_key: The API key to use for authentication, if not provided, the `MISTRAL_API_KEY` environment variable
                will be used if available.
            mistral_client: An existing `Mistral` client to use, if provided, `api_key` and `http_client` must be `None`.
            base_url: The base url for the Mistral requests.
            http_client: An existing async client to use for making HTTP requests.
        """
        if mistral_client is not None:
            assert http_client is None, 'Cannot provide both `mistral_client` and `http_client`'
            assert api_key is None, 'Cannot provide both `mistral_client` and `api_key`'
            assert base_url is None, 'Cannot provide both `mistral_client` and `base_url`'
            self._client = mistral_client
        else:
            api_key = api_key or os.getenv('MISTRAL_API_KEY')

            if not api_key:
                raise UserError(
                    'Set the `MISTRAL_API_KEY` environment variable or pass it via `MistralProvider(api_key=...)`'
                    'to use the Mistral provider.'
                )
            elif http_client is not None:
                self._client = Mistral(api_key=api_key, async_client=http_client, server_url=base_url)
            else:
                http_client = cached_async_http_client(provider='mistral')
                self._client = Mistral(api_key=api_key, async_client=http_client, server_url=base_url)

```
