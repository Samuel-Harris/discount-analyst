### OpenRouterProviderConfig

Bases: `TypedDict`

Represents the 'Provider' object from the OpenRouter API.

Source code in `pydantic_ai_slim/pydantic_ai/models/openrouter.py`

```python
class OpenRouterProviderConfig(TypedDict, total=False):
    """Represents the 'Provider' object from the OpenRouter API."""

    order: list[OpenRouterProviderName]
    """List of provider slugs to try in order (e.g. ["anthropic", "openai"]). [See details](https://openrouter.ai/docs/features/provider-routing#ordering-specific-providers)"""

    allow_fallbacks: bool
    """Whether to allow backup providers when the primary is unavailable. [See details](https://openrouter.ai/docs/features/provider-routing#disabling-fallbacks)"""

    require_parameters: bool
    """Only use providers that support all parameters in your request."""

    data_collection: Literal['allow', 'deny']
    """Control whether to use providers that may store data. [See details](https://openrouter.ai/docs/features/provider-routing#requiring-providers-to-comply-with-data-policies)"""

    zdr: bool
    """Restrict routing to only ZDR (Zero Data Retention) endpoints. [See details](https://openrouter.ai/docs/features/provider-routing#zero-data-retention-enforcement)"""

    only: list[OpenRouterProviderName]
    """List of provider slugs to allow for this request. [See details](https://openrouter.ai/docs/features/provider-routing#allowing-only-specific-providers)"""

    ignore: list[str]
    """List of provider slugs to skip for this request. [See details](https://openrouter.ai/docs/features/provider-routing#ignoring-providers)"""

    quantizations: list[Literal['int4', 'int8', 'fp4', 'fp6', 'fp8', 'fp16', 'bf16', 'fp32', 'unknown']]
    """List of quantization levels to filter by (e.g. ["int4", "int8"]). [See details](https://openrouter.ai/docs/features/provider-routing#quantization)"""

    sort: Literal['price', 'throughput', 'latency']
    """Sort providers by price or throughput. (e.g. "price" or "throughput"). [See details](https://openrouter.ai/docs/features/provider-routing#provider-sorting)"""

    max_price: _OpenRouterMaxPrice
    """The maximum pricing you want to pay for this request. [See details](https://openrouter.ai/docs/features/provider-routing#max-price)"""

```

#### order

```python
order: list[OpenRouterProviderName]

```

List of provider slugs to try in order (e.g. ["anthropic", "openai"]). [See details](https://openrouter.ai/docs/features/provider-routing#ordering-specific-providers)

#### allow_fallbacks

```python
allow_fallbacks: bool

```

Whether to allow backup providers when the primary is unavailable. [See details](https://openrouter.ai/docs/features/provider-routing#disabling-fallbacks)

#### require_parameters

```python
require_parameters: bool

```

Only use providers that support all parameters in your request.

#### data_collection

```python
data_collection: Literal['allow', 'deny']

```

Control whether to use providers that may store data. [See details](https://openrouter.ai/docs/features/provider-routing#requiring-providers-to-comply-with-data-policies)

#### zdr

```python
zdr: bool

```

Restrict routing to only ZDR (Zero Data Retention) endpoints. [See details](https://openrouter.ai/docs/features/provider-routing#zero-data-retention-enforcement)

#### only

```python
only: list[OpenRouterProviderName]

```

List of provider slugs to allow for this request. [See details](https://openrouter.ai/docs/features/provider-routing#allowing-only-specific-providers)

#### ignore

```python
ignore: list[str]

```

List of provider slugs to skip for this request. [See details](https://openrouter.ai/docs/features/provider-routing#ignoring-providers)

#### quantizations

```python
quantizations: list[
    Literal[
        "int4",
        "int8",
        "fp4",
        "fp6",
        "fp8",
        "fp16",
        "bf16",
        "fp32",
        "unknown",
    ]
]

```

List of quantization levels to filter by (e.g. ["int4", "int8"]). [See details](https://openrouter.ai/docs/features/provider-routing#quantization)

#### sort

```python
sort: Literal['price', 'throughput', 'latency']

```

Sort providers by price or throughput. (e.g. "price" or "throughput"). [See details](https://openrouter.ai/docs/features/provider-routing#provider-sorting)

#### max_price

```python
max_price: _OpenRouterMaxPrice

```

The maximum pricing you want to pay for this request. [See details](https://openrouter.ai/docs/features/provider-routing#max-price)
