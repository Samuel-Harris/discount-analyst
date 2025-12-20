### InstrumentedModel

Bases: `WrapperModel`

Model which wraps another model so that requests are instrumented with OpenTelemetry.

See the [Debugging and Monitoring guide](https://ai.pydantic.dev/logfire/) for more info.

Source code in `pydantic_ai_slim/pydantic_ai/models/instrumented.py`

```python
@dataclass(init=False)
class InstrumentedModel(WrapperModel):
    """Model which wraps another model so that requests are instrumented with OpenTelemetry.

    See the [Debugging and Monitoring guide](https://ai.pydantic.dev/logfire/) for more info.
    """

    instrumentation_settings: InstrumentationSettings
    """Instrumentation settings for this model."""

    def __init__(
        self,
        wrapped: Model | KnownModelName,
        options: InstrumentationSettings | None = None,
    ) -> None:
        super().__init__(wrapped)
        self.instrumentation_settings = options or InstrumentationSettings()

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        prepared_settings, prepared_parameters = self.wrapped.prepare_request(
            model_settings,
            model_request_parameters,
        )
        with self._instrument(messages, prepared_settings, prepared_parameters) as finish:
            response = await self.wrapped.request(messages, model_settings, model_request_parameters)
            finish(response, prepared_parameters)
            return response

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        prepared_settings, prepared_parameters = self.wrapped.prepare_request(
            model_settings,
            model_request_parameters,
        )
        with self._instrument(messages, prepared_settings, prepared_parameters) as finish:
            response_stream: StreamedResponse | None = None
            try:
                async with self.wrapped.request_stream(
                    messages, model_settings, model_request_parameters, run_context
                ) as response_stream:
                    yield response_stream
            finally:
                if response_stream:  # pragma: no branch
                    finish(response_stream.get(), prepared_parameters)

    @contextmanager
    def _instrument(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> Iterator[Callable[[ModelResponse, ModelRequestParameters], None]]:
        operation = 'chat'
        span_name = f'{operation} {self.model_name}'
        # TODO Missing attributes:
        #  - error.type: unclear if we should do something here or just always rely on span exceptions
        #  - gen_ai.request.stop_sequences/top_k: model_settings doesn't include these
        attributes: dict[str, AttributeValue] = {
            'gen_ai.operation.name': operation,
            **self.model_attributes(self.wrapped),
            **self.model_request_parameters_attributes(model_request_parameters),
            'logfire.json_schema': json.dumps(
                {
                    'type': 'object',
                    'properties': {'model_request_parameters': {'type': 'object'}},
                }
            ),
        }

        if model_settings:
            for key in MODEL_SETTING_ATTRIBUTES:
                if isinstance(value := model_settings.get(key), float | int):
                    attributes[f'gen_ai.request.{key}'] = value

        record_metrics: Callable[[], None] | None = None
        try:
            with self.instrumentation_settings.tracer.start_as_current_span(span_name, attributes=attributes) as span:

                def finish(response: ModelResponse, parameters: ModelRequestParameters):
                    # FallbackModel updates these span attributes.
                    attributes.update(getattr(span, 'attributes', {}))
                    request_model = attributes[GEN_AI_REQUEST_MODEL_ATTRIBUTE]
                    system = cast(str, attributes[GEN_AI_SYSTEM_ATTRIBUTE])

                    response_model = response.model_name or request_model
                    price_calculation = None

                    def _record_metrics():
                        metric_attributes = {
                            GEN_AI_SYSTEM_ATTRIBUTE: system,
                            'gen_ai.operation.name': operation,
                            'gen_ai.request.model': request_model,
                            'gen_ai.response.model': response_model,
                        }
                        self.instrumentation_settings.record_metrics(response, price_calculation, metric_attributes)

                    nonlocal record_metrics
                    record_metrics = _record_metrics

                    if not span.is_recording():
                        return

                    self.instrumentation_settings.handle_messages(messages, response, system, span, parameters)

                    attributes_to_set = {
                        **response.usage.opentelemetry_attributes(),
                        'gen_ai.response.model': response_model,
                    }
                    try:
                        price_calculation = response.cost()
                    except LookupError:
                        # The cost of this provider/model is unknown, which is common.
                        pass
                    except Exception as e:
                        warnings.warn(
                            f'Failed to get cost from response: {type(e).__name__}: {e}', CostCalculationFailedWarning
                        )
                    else:
                        attributes_to_set['operation.cost'] = float(price_calculation.total_price)

                    if response.provider_response_id is not None:
                        attributes_to_set['gen_ai.response.id'] = response.provider_response_id
                    if response.finish_reason is not None:
                        attributes_to_set['gen_ai.response.finish_reasons'] = [response.finish_reason]
                    span.set_attributes(attributes_to_set)
                    span.update_name(f'{operation} {request_model}')

                yield finish
        finally:
            if record_metrics:
                # We only want to record metrics after the span is finished,
                # to prevent them from being redundantly recorded in the span itself by logfire.
                record_metrics()

    @staticmethod
    def model_attributes(model: Model) -> dict[str, AttributeValue]:
        attributes: dict[str, AttributeValue] = {
            GEN_AI_SYSTEM_ATTRIBUTE: model.system,
            GEN_AI_REQUEST_MODEL_ATTRIBUTE: model.model_name,
        }
        if base_url := model.base_url:
            try:
                parsed = urlparse(base_url)
            except Exception:  # pragma: no cover
                pass
            else:
                if parsed.hostname:  # pragma: no branch
                    attributes['server.address'] = parsed.hostname
                if parsed.port:  # pragma: no branch
                    attributes['server.port'] = parsed.port

        return attributes

    @staticmethod
    def model_request_parameters_attributes(
        model_request_parameters: ModelRequestParameters,
    ) -> dict[str, AttributeValue]:
        return {'model_request_parameters': json.dumps(InstrumentedModel.serialize_any(model_request_parameters))}

    @staticmethod
    def event_to_dict(event: Event) -> dict[str, Any]:
        if not event.body:
            body = {}  # pragma: no cover
        elif isinstance(event.body, Mapping):
            body = event.body  # type: ignore
        else:
            body = {'body': event.body}
        return {**body, **(event.attributes or {})}

    @staticmethod
    def serialize_any(value: Any) -> str:
        try:
            return ANY_ADAPTER.dump_python(value, mode='json')
        except Exception:
            try:
                return str(value)
            except Exception as e:
                return f'Unable to serialize: {e}'

```

#### instrumentation_settings

```python
instrumentation_settings: InstrumentationSettings = (
    options or InstrumentationSettings()
)

```

Instrumentation settings for this model.
