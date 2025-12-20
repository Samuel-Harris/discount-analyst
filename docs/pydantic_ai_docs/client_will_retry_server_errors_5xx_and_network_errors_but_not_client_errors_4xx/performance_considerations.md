## Performance Considerations

- Retries add latency to requests, especially with exponential backoff
- Consider the total timeout for your application when configuring retry behavior
- Monitor retry rates to detect systemic issues
- Use async transports for better concurrency when handling multiple requests

For more advanced retry configurations, refer to the [tenacity documentation](https://tenacity.readthedocs.io/).
