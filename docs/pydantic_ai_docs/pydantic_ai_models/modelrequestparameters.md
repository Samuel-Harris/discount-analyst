### ModelRequestParameters

Configuration for an agent's request to a model, specifically related to tools and output handling.

Source code in `pydantic_ai_slim/pydantic_ai/models/__init__.py`

```python
@dataclass(repr=False, kw_only=True)
class ModelRequestParameters:
    """Configuration for an agent's request to a model, specifically related to tools and output handling."""

    function_tools: list[ToolDefinition] = field(default_factory=list)
    builtin_tools: list[AbstractBuiltinTool] = field(default_factory=list)

    output_mode: OutputMode = 'text'
    output_object: OutputObjectDefinition | None = None
    output_tools: list[ToolDefinition] = field(default_factory=list)
    prompted_output_template: str | None = None
    allow_text_output: bool = True
    allow_image_output: bool = False

    @cached_property
    def tool_defs(self) -> dict[str, ToolDefinition]:
        return {tool_def.name: tool_def for tool_def in [*self.function_tools, *self.output_tools]}

    @cached_property
    def prompted_output_instructions(self) -> str | None:
        if self.output_mode == 'prompted' and self.prompted_output_template and self.output_object:
            return PromptedOutputSchema.build_instructions(self.prompted_output_template, self.output_object)
        return None

    __repr__ = _utils.dataclasses_no_defaults_repr

```
