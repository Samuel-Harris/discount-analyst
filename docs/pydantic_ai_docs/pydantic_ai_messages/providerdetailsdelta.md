### ProviderDetailsDelta

```python
ProviderDetailsDelta: TypeAlias = (
    dict[str, Any]
    | Callable[[dict[str, Any] | None], dict[str, Any]]
    | None
)

```

Type for provider_details input: can be a static dict, a callback to update existing details, or None.
