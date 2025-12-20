result = agent.run_sync(
    'What is the capital of France?',
    deps={'location': None},
)
print(result.output)
#> The capital of France is Paris.

```
