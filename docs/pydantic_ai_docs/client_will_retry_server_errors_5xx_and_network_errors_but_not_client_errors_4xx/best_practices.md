## Best Practices

1. **Start Conservative**: Begin with a small number of retries (3-5) and reasonable wait times.
1. **Use Exponential Backoff**: This helps avoid overwhelming servers during outages.
1. **Set Maximum Wait Times**: Prevent indefinite delays with reasonable maximum wait times.
1. **Handle Rate Limits Properly**: Respect `Retry-After` headers when possible.
1. **Log Retry Attempts**: Add logging to monitor retry behavior in production. (This will be picked up by Logfire automatically if you instrument httpx.)
1. **Consider Circuit Breakers**: For high-traffic applications, consider implementing circuit breaker patterns.
