### StreamFunctionDef

```python
StreamFunctionDef: TypeAlias = Callable[
    [list[ModelMessage], AgentInfo],
    AsyncIterator[
        str
        | DeltaToolCalls
        | DeltaThinkingCalls
        | BuiltinToolCallsReturns
    ],
]

```

A function used to generate a streamed response.

While this is defined as having return type of `AsyncIterator[str | DeltaToolCalls | DeltaThinkingCalls | BuiltinTools]`, it should really be considered as `AsyncIterator[str] | AsyncIterator[DeltaToolCalls] | AsyncIterator[DeltaThinkingCalls]`,

E.g. you need to yield all text, all `DeltaToolCalls`, all `DeltaThinkingCalls`, or all `BuiltinToolCallsReturns`, not mix them.
