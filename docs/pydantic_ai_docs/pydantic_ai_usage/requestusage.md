### RequestUsage

Bases: `UsageBase`

LLM usage associated with a single request.

This is an implementation of `genai_prices.types.AbstractUsage` so it can be used to calculate the price of the request using [genai-prices](https://github.com/pydantic/genai-prices).

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
@dataclass(repr=False, kw_only=True)
class RequestUsage(UsageBase):
    """LLM usage associated with a single request.

    This is an implementation of `genai_prices.types.AbstractUsage` so it can be used to calculate the price of the
    request using [genai-prices](https://github.com/pydantic/genai-prices).
    """

    @property
    def requests(self):
        return 1

    def incr(self, incr_usage: RequestUsage) -> None:
        """Increment the usage in place.

        Args:
            incr_usage: The usage to increment by.
        """
        return _incr_usage_tokens(self, incr_usage)

    def __add__(self, other: RequestUsage) -> RequestUsage:
        """Add two RequestUsages together.

        This is provided so it's trivial to sum usage information from multiple parts of a response.

        **WARNING:** this CANNOT be used to sum multiple requests without breaking some pricing calculations.
        """
        new_usage = copy(self)
        new_usage.incr(other)
        return new_usage

    @classmethod
    def extract(
        cls,
        data: Any,
        *,
        provider: str,
        provider_url: str,
        provider_fallback: str,
        api_flavor: str = 'default',
        details: dict[str, Any] | None = None,
    ) -> RequestUsage:
        """Extract usage information from the response data using genai-prices.

        Args:
            data: The response data from the model API.
            provider: The actual provider ID
            provider_url: The provider base_url
            provider_fallback: The fallback provider ID to use if the actual provider is not found in genai-prices.
                For example, an OpenAI model should set this to "openai" in case it has an obscure provider ID.
            api_flavor: The API flavor to use when extracting usage information,
                e.g. 'chat' or 'responses' for OpenAI.
            details: Becomes the `details` field on the returned `RequestUsage` for convenience.
        """
        details = details or {}
        for provider_id, provider_api_url in [(None, provider_url), (provider, None), (provider_fallback, None)]:
            try:
                provider_obj = get_snapshot().find_provider(None, provider_id, provider_api_url)
                _model_ref, extracted_usage = provider_obj.extract_usage(data, api_flavor=api_flavor)
                return cls(**{k: v for k, v in extracted_usage.__dict__.items() if v is not None}, details=details)
            except Exception:
                pass
        return cls(details=details)

```

#### incr

```python
incr(incr_usage: RequestUsage) -> None

```

Increment the usage in place.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `incr_usage` | `RequestUsage` | The usage to increment by. | _required_ |

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
def incr(self, incr_usage: RequestUsage) -> None:
    """Increment the usage in place.

    Args:
        incr_usage: The usage to increment by.
    """
    return _incr_usage_tokens(self, incr_usage)

```

#### **add**

```python
__add__(other: RequestUsage) -> RequestUsage

```

Add two RequestUsages together.

This is provided so it's trivial to sum usage information from multiple parts of a response.

**WARNING:** this CANNOT be used to sum multiple requests without breaking some pricing calculations.

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
def __add__(self, other: RequestUsage) -> RequestUsage:
    """Add two RequestUsages together.

    This is provided so it's trivial to sum usage information from multiple parts of a response.

    **WARNING:** this CANNOT be used to sum multiple requests without breaking some pricing calculations.
    """
    new_usage = copy(self)
    new_usage.incr(other)
    return new_usage

```

#### extract

```python
extract(
    data: Any,
    *,
    provider: str,
    provider_url: str,
    provider_fallback: str,
    api_flavor: str = "default",
    details: dict[str, Any] | None = None
) -> RequestUsage

```

Extract usage information from the response data using genai-prices.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `data` | `Any` | The response data from the model API. | _required_ | | `provider` | `str` | The actual provider ID | _required_ | | `provider_url` | `str` | The provider base_url | _required_ | | `provider_fallback` | `str` | The fallback provider ID to use if the actual provider is not found in genai-prices. For example, an OpenAI model should set this to "openai" in case it has an obscure provider ID. | _required_ | | `api_flavor` | `str` | The API flavor to use when extracting usage information, e.g. 'chat' or 'responses' for OpenAI. | `'default'` | | `details` | `dict[str, Any] | None` | Becomes the details field on the returned RequestUsage for convenience. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/usage.py`

```python
@classmethod
def extract(
    cls,
    data: Any,
    *,
    provider: str,
    provider_url: str,
    provider_fallback: str,
    api_flavor: str = 'default',
    details: dict[str, Any] | None = None,
) -> RequestUsage:
    """Extract usage information from the response data using genai-prices.

    Args:
        data: The response data from the model API.
        provider: The actual provider ID
        provider_url: The provider base_url
        provider_fallback: The fallback provider ID to use if the actual provider is not found in genai-prices.
            For example, an OpenAI model should set this to "openai" in case it has an obscure provider ID.
        api_flavor: The API flavor to use when extracting usage information,
            e.g. 'chat' or 'responses' for OpenAI.
        details: Becomes the `details` field on the returned `RequestUsage` for convenience.
    """
    details = details or {}
    for provider_id, provider_api_url in [(None, provider_url), (provider, None), (provider_fallback, None)]:
        try:
            provider_obj = get_snapshot().find_provider(None, provider_id, provider_api_url)
            _model_ref, extracted_usage = provider_obj.extract_usage(data, api_flavor=api_flavor)
            return cls(**{k: v for k, v in extracted_usage.__dict__.items() if v is not None}, details=details)
        except Exception:
            pass
    return cls(details=details)

```
