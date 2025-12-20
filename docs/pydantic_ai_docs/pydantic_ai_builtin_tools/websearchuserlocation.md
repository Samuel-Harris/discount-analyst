### WebSearchUserLocation

Bases: `TypedDict`

Allows you to localize search results based on a user's location.

Supported by:

- Anthropic
- OpenAI Responses

Source code in `pydantic_ai_slim/pydantic_ai/builtin_tools.py`

```python
class WebSearchUserLocation(TypedDict, total=False):
    """Allows you to localize search results based on a user's location.

    Supported by:

    * Anthropic
    * OpenAI Responses
    """

    city: str
    """The city where the user is located."""

    country: str
    """The country where the user is located. For OpenAI, this must be a 2-letter country code (e.g., 'US', 'GB')."""

    region: str
    """The region or state where the user is located."""

    timezone: str
    """The timezone of the user's location."""

```

#### city

```python
city: str

```

The city where the user is located.

#### country

```python
country: str

```

The country where the user is located. For OpenAI, this must be a 2-letter country code (e.g., 'US', 'GB').

#### region

```python
region: str

```

The region or state where the user is located.

#### timezone

```python
timezone: str

```

The timezone of the user's location.
