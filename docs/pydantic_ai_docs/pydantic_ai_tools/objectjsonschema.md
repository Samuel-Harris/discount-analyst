### ObjectJsonSchema

```python
ObjectJsonSchema: TypeAlias = dict[str, Any]

```

Type representing JSON schema of an object, e.g. where `"type": "object"`.

This type is used to define tools parameters (aka arguments) in ToolDefinition.

With PEP-728 this should be a TypedDict with `type: Literal['object']`, and `extra_parts=Any`
