### ImageGenerationTool

Bases: `AbstractBuiltinTool`

A builtin tool that allows your agent to generate images.

Supported by:

- OpenAI Responses
- Google

Source code in `pydantic_ai_slim/pydantic_ai/builtin_tools.py`

```python
@dataclass(kw_only=True)
class ImageGenerationTool(AbstractBuiltinTool):
    """A builtin tool that allows your agent to generate images.

    Supported by:

    * OpenAI Responses
    * Google
    """

    background: Literal['transparent', 'opaque', 'auto'] = 'auto'
    """Background type for the generated image.

    Supported by:

    * OpenAI Responses. 'transparent' is only supported for 'png' and 'webp' output formats.
    """

    input_fidelity: Literal['high', 'low'] | None = None
    """
    Control how much effort the model will exert to match the style and features,
    especially facial features, of input images.

    Supported by:

    * OpenAI Responses. Default: 'low'.
    """

    moderation: Literal['auto', 'low'] = 'auto'
    """Moderation level for the generated image.

    Supported by:

    * OpenAI Responses
    """

    output_compression: int = 100
    """Compression level for the output image.

    Supported by:

    * OpenAI Responses. Only supported for 'png' and 'webp' output formats.
    """

    output_format: Literal['png', 'webp', 'jpeg'] | None = None
    """The output format of the generated image.

    Supported by:

    * OpenAI Responses. Default: 'png'.
    """

    partial_images: int = 0
    """
    Number of partial images to generate in streaming mode.

    Supported by:

    * OpenAI Responses. Supports 0 to 3.
    """

    quality: Literal['low', 'medium', 'high', 'auto'] = 'auto'
    """The quality of the generated image.

    Supported by:

    * OpenAI Responses
    """

    size: Literal['1024x1024', '1024x1536', '1536x1024', 'auto'] = 'auto'
    """The size of the generated image.

    Supported by:

    * OpenAI Responses
    """

    kind: str = 'image_generation'
    """The kind of tool."""

```

#### background

```python
background: Literal["transparent", "opaque", "auto"] = (
    "auto"
)

```

Background type for the generated image.

Supported by:

- OpenAI Responses. 'transparent' is only supported for 'png' and 'webp' output formats.

#### input_fidelity

```python
input_fidelity: Literal['high', 'low'] | None = None

```

Control how much effort the model will exert to match the style and features, especially facial features, of input images.

Supported by:

- OpenAI Responses. Default: 'low'.

#### moderation

```python
moderation: Literal['auto', 'low'] = 'auto'

```

Moderation level for the generated image.

Supported by:

- OpenAI Responses

#### output_compression

```python
output_compression: int = 100

```

Compression level for the output image.

Supported by:

- OpenAI Responses. Only supported for 'png' and 'webp' output formats.

#### output_format

```python
output_format: Literal['png', 'webp', 'jpeg'] | None = None

```

The output format of the generated image.

Supported by:

- OpenAI Responses. Default: 'png'.

#### partial_images

```python
partial_images: int = 0

```

Number of partial images to generate in streaming mode.

Supported by:

- OpenAI Responses. Supports 0 to 3.

#### quality

```python
quality: Literal['low', 'medium', 'high', 'auto'] = 'auto'

```

The quality of the generated image.

Supported by:

- OpenAI Responses

#### size

```python
size: Literal[
    "1024x1024", "1024x1536", "1536x1024", "auto"
] = "auto"

```

The size of the generated image.

Supported by:

- OpenAI Responses

#### kind

```python
kind: str = 'image_generation'

```

The kind of tool.
