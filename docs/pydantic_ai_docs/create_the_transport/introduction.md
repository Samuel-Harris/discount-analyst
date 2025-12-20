transport = TenacityTransport(
    config=RetryConfig(stop=stop_after_attempt(3), reraise=True),
    validate_response=validator
)
