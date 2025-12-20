### AnthropicJsonSchemaTransformer

Bases: `JsonSchemaTransformer`

Transforms schemas to the subset supported by Anthropic structured outputs.

Transformation is applied when:

- `NativeOutput` is used as the `output_type` of the Agent
- `strict=True` is set on the `Tool`

The behavior of this transformer differs from the OpenAI one in that it sets `Tool.strict=False` by default when not explicitly set to True.

Example

```python
from pydantic_ai import Agent

agent = Agent('anthropic:claude-sonnet-4-5')

@agent.tool_plain  # -> defaults to strict=False
def my_tool(x: str) -> dict[str, int]:
    ...

```

Anthropic's SDK `transform_schema()` automatically:

- Adds `additionalProperties: false` to all objects (required by API)
- Removes unsupported constraints (minLength, pattern, etc.)
- Moves removed constraints to description field
- Removes title and $schema fields

Source code in `pydantic_ai_slim/pydantic_ai/profiles/anthropic.py`

````python
@dataclass(init=False)
class AnthropicJsonSchemaTransformer(JsonSchemaTransformer):
    """Transforms schemas to the subset supported by Anthropic structured outputs.

    Transformation is applied when:
    - `NativeOutput` is used as the `output_type` of the Agent
    - `strict=True` is set on the `Tool`

    The behavior of this transformer differs from the OpenAI one in that it sets `Tool.strict=False` by default when not explicitly set to True.

    Example:
        ```python
        from pydantic_ai import Agent

        agent = Agent('anthropic:claude-sonnet-4-5')

        @agent.tool_plain  # -> defaults to strict=False
        def my_tool(x: str) -> dict[str, int]:
            ...
        ```

    Anthropic's SDK `transform_schema()` automatically:
    - Adds `additionalProperties: false` to all objects (required by API)
    - Removes unsupported constraints (minLength, pattern, etc.)
    - Moves removed constraints to description field
    - Removes title and $schema fields
    """

    def walk(self) -> JsonSchema:
        from anthropic import transform_schema

        schema = super().walk()

        # The caller (pydantic_ai.models._customize_tool_def or _customize_output_object) coalesces
        # - output_object.strict = self.is_strict_compatible
        # - tool_def.strict = self.is_strict_compatible
        # the reason we don't default to `strict=True` is that the transformation could be lossy
        # so in order to change the behavior (default to True), we need to come up with logic that will check for lossiness
        # https://github.com/pydantic/pydantic-ai/issues/3541
        self.is_strict_compatible = self.strict is True  # not compatible when strict is False/None

        return transform_schema(schema) if self.strict is True else schema

    def transform(self, schema: JsonSchema) -> JsonSchema:
        schema.pop('title', None)
        schema.pop('$schema', None)
        return schema

````
