### ToolFuncPlain

```python
ToolFuncPlain: TypeAlias = Callable[ToolParams, Any]

```

A tool function that does not take `RunContext` as the first argument.

Usage `ToolPlainFunc[ToolParams]`.
