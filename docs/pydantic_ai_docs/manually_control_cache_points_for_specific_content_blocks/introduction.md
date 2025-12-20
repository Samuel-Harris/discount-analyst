result = agent.run_sync([
    'Long context from documentation...',
    CachePoint(),  # Cache everything up to this point
    'First question'
])
print(result.output)

```
