### LogfirePlugin

Bases: `SimplePlugin`

Temporal client plugin for Logfire.

Source code in `pydantic_ai_slim/pydantic_ai/durable_exec/temporal/_logfire.py`

```python
class LogfirePlugin(SimplePlugin):
    """Temporal client plugin for Logfire."""

    def __init__(self, setup_logfire: Callable[[], Logfire] = _default_setup_logfire, *, metrics: bool = True):
        try:
            import logfire  # noqa: F401 # pyright: ignore[reportUnusedImport]
            from opentelemetry.trace import get_tracer
            from temporalio.contrib.opentelemetry import TracingInterceptor
        except ImportError as _import_error:
            raise ImportError(
                'Please install the `logfire` package to use the Logfire plugin, '
                'you can use the `logfire` optional group â€” `pip install "pydantic-ai-slim[logfire]"`'
            ) from _import_error

        self.setup_logfire = setup_logfire
        self.metrics = metrics

        super().__init__(  # type: ignore[reportUnknownMemberType]
            name='LogfirePlugin',
            client_interceptors=[TracingInterceptor(get_tracer('temporalio'))],
        )

    async def connect_service_client(
        self, config: ConnectConfig, next: Callable[[ConnectConfig], Awaitable[ServiceClient]]
    ) -> ServiceClient:
        logfire = self.setup_logfire()

        if self.metrics:
            logfire_config = logfire.config
            token = logfire_config.token
            if logfire_config.send_to_logfire and token is not None and logfire_config.metrics is not False:
                base_url = logfire_config.advanced.generate_base_url(token)
                metrics_url = base_url + '/v1/metrics'
                headers = {'Authorization': f'Bearer {token}'}

                config.runtime = Runtime(
                    telemetry=TelemetryConfig(metrics=OpenTelemetryConfig(url=metrics_url, headers=headers))
                )

        return await next(config)

```
