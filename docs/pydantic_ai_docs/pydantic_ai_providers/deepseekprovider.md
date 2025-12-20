### DeepSeekProvider

Bases: `Provider[AsyncOpenAI]`

Provider for DeepSeek API.

Source code in `pydantic_ai_slim/pydantic_ai/providers/deepseek.py`

```python
class DeepSeekProvider(Provider[AsyncOpenAI]):
    """Provider for DeepSeek API."""

    @property
    def name(self) -> str:
        return 'deepseek'

    @property
    def base_url(self) -> str:
        return 'https://api.deepseek.com'

    @property
    def client(self) -> AsyncOpenAI:
        return self._client

    def model_profile(self, model_name: str) -> ModelProfile | None:
        profile = deepseek_model_profile(model_name)

        # As DeepSeekProvider is always used with OpenAIChatModel, which used to unconditionally use OpenAIJsonSchemaTransformer,
        # we need to maintain that behavior unless json_schema_transformer is set explicitly.
        # This was not the case when using a DeepSeek model with another model class (e.g. BedrockConverseModel or GroqModel),
        # so we won't do this in `deepseek_model_profile` unless we learn it's always needed.
        return OpenAIModelProfile(
            json_schema_transformer=OpenAIJsonSchemaTransformer,
            supports_json_object_output=True,
            openai_chat_thinking_field='reasoning_content',
            # Starting from DeepSeek v3.2, DeepSeek requires sending thinking parts for optimal agentic performance.
            openai_chat_send_back_thinking_parts='field',
            # DeepSeek v3.2 reasoning mode does not support tool_choice=required yet
            openai_supports_tool_choice_required=(model_name != 'deepseek-reasoner'),
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
        api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        if not api_key and openai_client is None:
            raise UserError(
                'Set the `DEEPSEEK_API_KEY` environment variable or pass it via `DeepSeekProvider(api_key=...)`'
                'to use the DeepSeek provider.'
            )

        if openai_client is not None:
            self._client = openai_client
        elif http_client is not None:
            self._client = AsyncOpenAI(base_url=self.base_url, api_key=api_key, http_client=http_client)
        else:
            http_client = cached_async_http_client(provider='deepseek')
            self._client = AsyncOpenAI(base_url=self.base_url, api_key=api_key, http_client=http_client)

```
