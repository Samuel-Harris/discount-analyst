### ModelSettings

Bases: `TypedDict`

Settings to configure an LLM.

Here we include only settings which apply to multiple models / model providers, though not all of these settings are supported by all models.

Source code in `pydantic_ai_slim/pydantic_ai/settings.py`

```python
class ModelSettings(TypedDict, total=False):
    """Settings to configure an LLM.

    Here we include only settings which apply to multiple models / model providers,
    though not all of these settings are supported by all models.
    """

    max_tokens: int
    """The maximum number of tokens to generate before stopping.

    Supported by:

    * Gemini
    * Anthropic
    * OpenAI
    * Groq
    * Cohere
    * Mistral
    * Bedrock
    * MCP Sampling
    * Outlines (all providers)
    """

    temperature: float
    """Amount of randomness injected into the response.

    Use `temperature` closer to `0.0` for analytical / multiple choice, and closer to a model's
    maximum `temperature` for creative and generative tasks.

    Note that even with `temperature` of `0.0`, the results will not be fully deterministic.

    Supported by:

    * Gemini
    * Anthropic
    * OpenAI
    * Groq
    * Cohere
    * Mistral
    * Bedrock
    * Outlines (Transformers, LlamaCpp, SgLang, VLLMOffline)
    """

    top_p: float
    """An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass.

    So 0.1 means only the tokens comprising the top 10% probability mass are considered.

    You should either alter `temperature` or `top_p`, but not both.

    Supported by:

    * Gemini
    * Anthropic
    * OpenAI
    * Groq
    * Cohere
    * Mistral
    * Bedrock
    * Outlines (Transformers, LlamaCpp, SgLang, VLLMOffline)
    """

    timeout: float | Timeout
    """Override the client-level default timeout for a request, in seconds.

    Supported by:

    * Gemini
    * Anthropic
    * OpenAI
    * Groq
    * Mistral
    """

    parallel_tool_calls: bool
    """Whether to allow parallel tool calls.

    Supported by:

    * OpenAI (some models, not o1)
    * Groq
    * Anthropic
    """

    seed: int
    """The random seed to use for the model, theoretically allowing for deterministic results.

    Supported by:

    * OpenAI
    * Groq
    * Cohere
    * Mistral
    * Gemini
    * Outlines (LlamaCpp, VLLMOffline)
    """

    presence_penalty: float
    """Penalize new tokens based on whether they have appeared in the text so far.

    Supported by:

    * OpenAI
    * Groq
    * Cohere
    * Gemini
    * Mistral
    * Outlines (LlamaCpp, SgLang, VLLMOffline)
    """

    frequency_penalty: float
    """Penalize new tokens based on their existing frequency in the text so far.

    Supported by:

    * OpenAI
    * Groq
    * Cohere
    * Gemini
    * Mistral
    * Outlines (LlamaCpp, SgLang, VLLMOffline)
    """

    logit_bias: dict[str, int]
    """Modify the likelihood of specified tokens appearing in the completion.

    Supported by:

    * OpenAI
    * Groq
    * Outlines (Transformers, LlamaCpp, VLLMOffline)
    """

    stop_sequences: list[str]
    """Sequences that will cause the model to stop generating.

    Supported by:

    * OpenAI
    * Anthropic
    * Bedrock
    * Mistral
    * Groq
    * Cohere
    * Google
    """

    extra_headers: dict[str, str]
    """Extra headers to send to the model.

    Supported by:

    * OpenAI
    * Anthropic
    * Groq
    """

    extra_body: object
    """Extra body to send to the model.

    Supported by:

    * OpenAI
    * Anthropic
    * Groq
    * Outlines (all providers)
    """

```

#### max_tokens

```python
max_tokens: int

```

The maximum number of tokens to generate before stopping.

Supported by:

- Gemini
- Anthropic
- OpenAI
- Groq
- Cohere
- Mistral
- Bedrock
- MCP Sampling
- Outlines (all providers)

#### temperature

```python
temperature: float

```

Amount of randomness injected into the response.

Use `temperature` closer to `0.0` for analytical / multiple choice, and closer to a model's maximum `temperature` for creative and generative tasks.

Note that even with `temperature` of `0.0`, the results will not be fully deterministic.

Supported by:

- Gemini
- Anthropic
- OpenAI
- Groq
- Cohere
- Mistral
- Bedrock
- Outlines (Transformers, LlamaCpp, SgLang, VLLMOffline)

#### top_p

```python
top_p: float

```

An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass.

So 0.1 means only the tokens comprising the top 10% probability mass are considered.

You should either alter `temperature` or `top_p`, but not both.

Supported by:

- Gemini
- Anthropic
- OpenAI
- Groq
- Cohere
- Mistral
- Bedrock
- Outlines (Transformers, LlamaCpp, SgLang, VLLMOffline)

#### timeout

```python
timeout: float | Timeout

```

Override the client-level default timeout for a request, in seconds.

Supported by:

- Gemini
- Anthropic
- OpenAI
- Groq
- Mistral

#### parallel_tool_calls

```python
parallel_tool_calls: bool

```

Whether to allow parallel tool calls.

Supported by:

- OpenAI (some models, not o1)
- Groq
- Anthropic

#### seed

```python
seed: int

```

The random seed to use for the model, theoretically allowing for deterministic results.

Supported by:

- OpenAI
- Groq
- Cohere
- Mistral
- Gemini
- Outlines (LlamaCpp, VLLMOffline)

#### presence_penalty

```python
presence_penalty: float

```

Penalize new tokens based on whether they have appeared in the text so far.

Supported by:

- OpenAI
- Groq
- Cohere
- Gemini
- Mistral
- Outlines (LlamaCpp, SgLang, VLLMOffline)

#### frequency_penalty

```python
frequency_penalty: float

```

Penalize new tokens based on their existing frequency in the text so far.

Supported by:

- OpenAI
- Groq
- Cohere
- Gemini
- Mistral
- Outlines (LlamaCpp, SgLang, VLLMOffline)

#### logit_bias

```python
logit_bias: dict[str, int]

```

Modify the likelihood of specified tokens appearing in the completion.

Supported by:

- OpenAI
- Groq
- Outlines (Transformers, LlamaCpp, VLLMOffline)

#### stop_sequences

```python
stop_sequences: list[str]

```

Sequences that will cause the model to stop generating.

Supported by:

- OpenAI
- Anthropic
- Bedrock
- Mistral
- Groq
- Cohere
- Google

#### extra_headers

```python
extra_headers: dict[str, str]

```

Extra headers to send to the model.

Supported by:

- OpenAI
- Anthropic
- Groq

#### extra_body

```python
extra_body: object

```

Extra body to send to the model.

Supported by:

- OpenAI
- Anthropic
- Groq
- Outlines (all providers)
