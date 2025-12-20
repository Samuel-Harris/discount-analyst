### AbstractBuiltinTool

Bases: `ABC`

A builtin tool that can be used by an agent.

This class is abstract and cannot be instantiated directly.

The builtin tools are passed to the model as part of the `ModelRequestParameters`.

Source code in `pydantic_ai_slim/pydantic_ai/builtin_tools.py`

```python
@dataclass(kw_only=True)
class AbstractBuiltinTool(ABC):
    """A builtin tool that can be used by an agent.

    This class is abstract and cannot be instantiated directly.

    The builtin tools are passed to the model as part of the `ModelRequestParameters`.
    """

    kind: str = 'unknown_builtin_tool'
    """Built-in tool identifier, this should be available on all built-in tools as a discriminator."""

    @property
    def unique_id(self) -> str:
        """A unique identifier for the builtin tool.

        If multiple instances of the same builtin tool can be passed to the model, subclasses should override this property to allow them to be distinguished.
        """
        return self.kind

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        _BUILTIN_TOOL_TYPES[cls.kind] = cls

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, handler: pydantic.GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        if cls is not AbstractBuiltinTool:
            return handler(cls)

        tools = _BUILTIN_TOOL_TYPES.values()
        if len(tools) == 1:  # pragma: no cover
            tools_type = next(iter(tools))
        else:
            tools_annotated = [Annotated[tool, pydantic.Tag(tool.kind)] for tool in tools]
            tools_type = Annotated[Union[tuple(tools_annotated)], pydantic.Discriminator(_tool_discriminator)]  # noqa: UP007

        return handler(tools_type)

```

#### kind

```python
kind: str = 'unknown_builtin_tool'

```

Built-in tool identifier, this should be available on all built-in tools as a discriminator.

#### unique_id

```python
unique_id: str

```

A unique identifier for the builtin tool.

If multiple instances of the same builtin tool can be passed to the model, subclasses should override this property to allow them to be distinguished.
