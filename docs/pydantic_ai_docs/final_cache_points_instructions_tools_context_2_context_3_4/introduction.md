print(result.output)
usage = result.usage()
print(f'Cache write tokens: {usage.cache_write_tokens}')
print(f'Cache read tokens: {usage.cache_read_tokens}')

```

**Key Points**:

- System and tool cache points are **always preserved**
- The cache point created by `anthropic_cache_messages` is **always preserved** (as it's the newest message cache point)
- Additional `CachePoint` markers in messages are removed from oldest to newest when the limit is exceeded
- This ensures critical caching (instructions/tools) is maintained while still benefiting from message-level caching
