result2 = agent.run_sync('What is the capital of Germany?')
print(f'Cache write: {result1.usage().cache_write_tokens}')
print(f'Cache read: {result2.usage().cache_read_tokens}')

```
