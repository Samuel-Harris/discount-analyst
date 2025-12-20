### EndStrategy

```python
EndStrategy = Literal['early', 'exhaustive']

```

The strategy for handling multiple tool calls when a final result is found.

- `'early'`: Stop processing other tool calls once a final result is found
- `'exhaustive'`: Process all tool calls even after finding a final result
