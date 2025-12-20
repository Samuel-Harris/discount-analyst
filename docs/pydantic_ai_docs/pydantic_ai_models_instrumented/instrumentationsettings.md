### InstrumentationSettings

Options for instrumenting models and agents with OpenTelemetry.

Used in:

- `Agent(instrument=...)`
- Agent.instrument_all()
- InstrumentedModel

See the [Debugging and Monitoring guide](https://ai.pydantic.dev/logfire/) for more info.

Source code in `pydantic_ai_slim/pydantic_ai/models/instrumented.py`

```python
@dataclass(init=False)
class InstrumentationSettings:
    """Options for instrumenting models and agents with OpenTelemetry.

    Used in:

    - `Agent(instrument=...)`
    - [`Agent.instrument_all()`][pydantic_ai.agent.Agent.instrument_all]
    - [`InstrumentedModel`][pydantic_ai.models.instrumented.InstrumentedModel]

    See the [Debugging and Monitoring guide](https://ai.pydantic.dev/logfire/) for more info.
    """

    tracer: Tracer = field(repr=False)
    event_logger: EventLogger = field(repr=False)
    event_mode: Literal['attributes', 'logs'] = 'attributes'
    include_binary_content: bool = True
    include_content: bool = True
    version: Literal[1, 2, 3] = DEFAULT_INSTRUMENTATION_VERSION

    def __init__(
        self,
        *,
        tracer_provider: TracerProvider | None = None,
        meter_provider: MeterProvider | None = None,
        include_binary_content: bool = True,
        include_content: bool = True,
        version: Literal[1, 2, 3] = DEFAULT_INSTRUMENTATION_VERSION,
        event_mode: Literal['attributes', 'logs'] = 'attributes',
        event_logger_provider: EventLoggerProvider | None = None,
    ):
        """Create instrumentation options.

        Args:
            tracer_provider: The OpenTelemetry tracer provider to use.
                If not provided, the global tracer provider is used.
                Calling `logfire.configure()` sets the global tracer provider, so most users don't need this.
            meter_provider: The OpenTelemetry meter provider to use.
                If not provided, the global meter provider is used.
                Calling `logfire.configure()` sets the global meter provider, so most users don't need this.
            include_binary_content: Whether to include binary content in the instrumentation events.
            include_content: Whether to include prompts, completions, and tool call arguments and responses
                in the instrumentation events.
            version: Version of the data format. This is unrelated to the Pydantic AI package version.
                Version 1 is based on the legacy event-based OpenTelemetry GenAI spec
                    and will be removed in a future release.
                    The parameters `event_mode` and `event_logger_provider` are only relevant for version 1.
                Version 2 uses the newer OpenTelemetry GenAI spec and stores messages in the following attributes:
                    - `gen_ai.system_instructions` for instructions passed to the agent.
                    - `gen_ai.input.messages` and `gen_ai.output.messages` on model request spans.
                    - `pydantic_ai.all_messages` on agent run spans.
            event_mode: The mode for emitting events in version 1.
                If `'attributes'`, events are attached to the span as attributes.
                If `'logs'`, events are emitted as OpenTelemetry log-based events.
            event_logger_provider: The OpenTelemetry event logger provider to use.
                If not provided, the global event logger provider is used.
                Calling `logfire.configure()` sets the global event logger provider, so most users don't need this.
                This is only used if `event_mode='logs'` and `version=1`.
        """
        from pydantic_ai import __version__

        tracer_provider = tracer_provider or get_tracer_provider()
        meter_provider = meter_provider or get_meter_provider()
        event_logger_provider = event_logger_provider or get_event_logger_provider()
        scope_name = 'pydantic-ai'
        self.tracer = tracer_provider.get_tracer(scope_name, __version__)
        self.meter = meter_provider.get_meter(scope_name, __version__)
        self.event_logger = event_logger_provider.get_event_logger(scope_name, __version__)
        self.event_mode = event_mode
        self.include_binary_content = include_binary_content
        self.include_content = include_content

        if event_mode == 'logs' and version != 1:
            warnings.warn(
                'event_mode is only relevant for version=1 which is deprecated and will be removed in a future release.',
                stacklevel=2,
            )
            version = 1

        self.version = version

        # As specified in the OpenTelemetry GenAI metrics spec:
        # https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/#metric-gen_aiclienttokenusage
        tokens_histogram_kwargs = dict(
            name='gen_ai.client.token.usage',
            unit='{token}',
            description='Measures number of input and output tokens used',
        )
        try:
            self.tokens_histogram = self.meter.create_histogram(
                **tokens_histogram_kwargs,
                explicit_bucket_boundaries_advisory=TOKEN_HISTOGRAM_BOUNDARIES,
            )
        except TypeError:  # pragma: lax no cover
            # Older OTel/logfire versions don't support explicit_bucket_boundaries_advisory
            self.tokens_histogram = self.meter.create_histogram(
                **tokens_histogram_kwargs,  # pyright: ignore
            )
        self.cost_histogram = self.meter.create_histogram(
            'operation.cost',
            unit='{USD}',
            description='Monetary cost',
        )

    def messages_to_otel_events(
        self, messages: list[ModelMessage], parameters: ModelRequestParameters | None = None
    ) -> list[Event]:
        """Convert a list of model messages to OpenTelemetry events.

        Args:
            messages: The messages to convert.
            parameters: The model request parameters.

        Returns:
            A list of OpenTelemetry events.
        """
        events: list[Event] = []
        instructions = InstrumentedModel._get_instructions(messages, parameters)  # pyright: ignore [reportPrivateUsage]
        if instructions is not None:
            events.append(
                Event(
                    'gen_ai.system.message',
                    body={**({'content': instructions} if self.include_content else {}), 'role': 'system'},
                )
            )

        for message_index, message in enumerate(messages):
            message_events: list[Event] = []
            if isinstance(message, ModelRequest):
                for part in message.parts:
                    if hasattr(part, 'otel_event'):
                        message_events.append(part.otel_event(self))
            elif isinstance(message, ModelResponse):  # pragma: no branch
                message_events = message.otel_events(self)
            for event in message_events:
                event.attributes = {
                    'gen_ai.message.index': message_index,
                    **(event.attributes or {}),
                }
            events.extend(message_events)

        for event in events:
            event.body = InstrumentedModel.serialize_any(event.body)
        return events

    def messages_to_otel_messages(self, messages: list[ModelMessage]) -> list[_otel_messages.ChatMessage]:
        result: list[_otel_messages.ChatMessage] = []
        for message in messages:
            if isinstance(message, ModelRequest):
                for is_system, group in itertools.groupby(message.parts, key=lambda p: isinstance(p, SystemPromptPart)):
                    message_parts: list[_otel_messages.MessagePart] = []
                    for part in group:
                        if hasattr(part, 'otel_message_parts'):
                            message_parts.extend(part.otel_message_parts(self))
                    result.append(
                        _otel_messages.ChatMessage(role='system' if is_system else 'user', parts=message_parts)
                    )
            elif isinstance(message, ModelResponse):  # pragma: no branch
                otel_message = _otel_messages.OutputMessage(role='assistant', parts=message.otel_message_parts(self))
                if message.finish_reason is not None:
                    otel_message['finish_reason'] = message.finish_reason
                result.append(otel_message)
        return result

    def handle_messages(
        self,
        input_messages: list[ModelMessage],
        response: ModelResponse,
        system: str,
        span: Span,
        parameters: ModelRequestParameters | None = None,
    ):
        if self.version == 1:
            events = self.messages_to_otel_events(input_messages, parameters)
            for event in self.messages_to_otel_events([response], parameters):
                events.append(
                    Event(
                        'gen_ai.choice',
                        body={
                            'index': 0,
                            'message': event.body,
                        },
                    )
                )
            for event in events:
                event.attributes = {
                    GEN_AI_SYSTEM_ATTRIBUTE: system,
                    **(event.attributes or {}),
                }
            self._emit_events(span, events)
        else:
            output_messages = self.messages_to_otel_messages([response])
            assert len(output_messages) == 1
            output_message = output_messages[0]
            instructions = InstrumentedModel._get_instructions(input_messages, parameters)  # pyright: ignore [reportPrivateUsage]
            system_instructions_attributes = self.system_instructions_attributes(instructions)
            attributes: dict[str, AttributeValue] = {
                'gen_ai.input.messages': json.dumps(self.messages_to_otel_messages(input_messages)),
                'gen_ai.output.messages': json.dumps([output_message]),
                **system_instructions_attributes,
                'logfire.json_schema': json.dumps(
                    {
                        'type': 'object',
                        'properties': {
                            'gen_ai.input.messages': {'type': 'array'},
                            'gen_ai.output.messages': {'type': 'array'},
                            **(
                                {'gen_ai.system_instructions': {'type': 'array'}}
                                if system_instructions_attributes
                                else {}
                            ),
                            'model_request_parameters': {'type': 'object'},
                        },
                    }
                ),
            }
            span.set_attributes(attributes)

    def system_instructions_attributes(self, instructions: str | None) -> dict[str, str]:
        if instructions and self.include_content:
            return {
                'gen_ai.system_instructions': json.dumps([_otel_messages.TextPart(type='text', content=instructions)]),
            }
        return {}

    def _emit_events(self, span: Span, events: list[Event]) -> None:
        if self.event_mode == 'logs':
            for event in events:
                self.event_logger.emit(event)
        else:
            attr_name = 'events'
            span.set_attributes(
                {
                    attr_name: json.dumps([InstrumentedModel.event_to_dict(event) for event in events]),
                    'logfire.json_schema': json.dumps(
                        {
                            'type': 'object',
                            'properties': {
                                attr_name: {'type': 'array'},
                                'model_request_parameters': {'type': 'object'},
                            },
                        }
                    ),
                }
            )

    def record_metrics(
        self,
        response: ModelResponse,
        price_calculation: PriceCalculation | None,
        attributes: dict[str, AttributeValue],
    ):
        for typ in ['input', 'output']:
            if not (tokens := getattr(response.usage, f'{typ}_tokens', 0)):  # pragma: no cover
                continue
            token_attributes = {**attributes, 'gen_ai.token.type': typ}
            self.tokens_histogram.record(tokens, token_attributes)
            if price_calculation:
                cost = float(getattr(price_calculation, f'{typ}_price'))
                self.cost_histogram.record(cost, token_attributes)

```

#### **init**

```python
__init__(
    *,
    tracer_provider: TracerProvider | None = None,
    meter_provider: MeterProvider | None = None,
    include_binary_content: bool = True,
    include_content: bool = True,
    version: Literal[
        1, 2, 3
    ] = DEFAULT_INSTRUMENTATION_VERSION,
    event_mode: Literal[
        "attributes", "logs"
    ] = "attributes",
    event_logger_provider: EventLoggerProvider | None = None
)

```

Create instrumentation options.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `tracer_provider` | `TracerProvider | None` | The OpenTelemetry tracer provider to use. If not provided, the global tracer provider is used. Calling logfire.configure() sets the global tracer provider, so most users don't need this. | `None` | | `meter_provider` | `MeterProvider | None` | The OpenTelemetry meter provider to use. If not provided, the global meter provider is used. Calling logfire.configure() sets the global meter provider, so most users don't need this. | `None` | | `include_binary_content` | `bool` | Whether to include binary content in the instrumentation events. | `True` | | `include_content` | `bool` | Whether to include prompts, completions, and tool call arguments and responses in the instrumentation events. | `True` | | `version` | `Literal[1, 2, 3]` | Version of the data format. This is unrelated to the Pydantic AI package version. Version 1 is based on the legacy event-based OpenTelemetry GenAI spec and will be removed in a future release. The parameters event_mode and event_logger_provider are only relevant for version 1. Version 2 uses the newer OpenTelemetry GenAI spec and stores messages in the following attributes: - gen_ai.system_instructions for instructions passed to the agent. - gen_ai.input.messages and gen_ai.output.messages on model request spans. - pydantic_ai.all_messages on agent run spans. | `DEFAULT_INSTRUMENTATION_VERSION` | | `event_mode` | `Literal['attributes', 'logs']` | The mode for emitting events in version 1. If 'attributes', events are attached to the span as attributes. If 'logs', events are emitted as OpenTelemetry log-based events. | `'attributes'` | | `event_logger_provider` | `EventLoggerProvider | None` | The OpenTelemetry event logger provider to use. If not provided, the global event logger provider is used. Calling logfire.configure() sets the global event logger provider, so most users don't need this. This is only used if event_mode='logs' and version=1. | `None` |

Source code in `pydantic_ai_slim/pydantic_ai/models/instrumented.py`

```python
def __init__(
    self,
    *,
    tracer_provider: TracerProvider | None = None,
    meter_provider: MeterProvider | None = None,
    include_binary_content: bool = True,
    include_content: bool = True,
    version: Literal[1, 2, 3] = DEFAULT_INSTRUMENTATION_VERSION,
    event_mode: Literal['attributes', 'logs'] = 'attributes',
    event_logger_provider: EventLoggerProvider | None = None,
):
    """Create instrumentation options.

    Args:
        tracer_provider: The OpenTelemetry tracer provider to use.
            If not provided, the global tracer provider is used.
            Calling `logfire.configure()` sets the global tracer provider, so most users don't need this.
        meter_provider: The OpenTelemetry meter provider to use.
            If not provided, the global meter provider is used.
            Calling `logfire.configure()` sets the global meter provider, so most users don't need this.
        include_binary_content: Whether to include binary content in the instrumentation events.
        include_content: Whether to include prompts, completions, and tool call arguments and responses
            in the instrumentation events.
        version: Version of the data format. This is unrelated to the Pydantic AI package version.
            Version 1 is based on the legacy event-based OpenTelemetry GenAI spec
                and will be removed in a future release.
                The parameters `event_mode` and `event_logger_provider` are only relevant for version 1.
            Version 2 uses the newer OpenTelemetry GenAI spec and stores messages in the following attributes:
                - `gen_ai.system_instructions` for instructions passed to the agent.
                - `gen_ai.input.messages` and `gen_ai.output.messages` on model request spans.
                - `pydantic_ai.all_messages` on agent run spans.
        event_mode: The mode for emitting events in version 1.
            If `'attributes'`, events are attached to the span as attributes.
            If `'logs'`, events are emitted as OpenTelemetry log-based events.
        event_logger_provider: The OpenTelemetry event logger provider to use.
            If not provided, the global event logger provider is used.
            Calling `logfire.configure()` sets the global event logger provider, so most users don't need this.
            This is only used if `event_mode='logs'` and `version=1`.
    """
    from pydantic_ai import __version__

    tracer_provider = tracer_provider or get_tracer_provider()
    meter_provider = meter_provider or get_meter_provider()
    event_logger_provider = event_logger_provider or get_event_logger_provider()
    scope_name = 'pydantic-ai'
    self.tracer = tracer_provider.get_tracer(scope_name, __version__)
    self.meter = meter_provider.get_meter(scope_name, __version__)
    self.event_logger = event_logger_provider.get_event_logger(scope_name, __version__)
    self.event_mode = event_mode
    self.include_binary_content = include_binary_content
    self.include_content = include_content

    if event_mode == 'logs' and version != 1:
        warnings.warn(
            'event_mode is only relevant for version=1 which is deprecated and will be removed in a future release.',
            stacklevel=2,
        )
        version = 1

    self.version = version

    # As specified in the OpenTelemetry GenAI metrics spec:
    # https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/#metric-gen_aiclienttokenusage
    tokens_histogram_kwargs = dict(
        name='gen_ai.client.token.usage',
        unit='{token}',
        description='Measures number of input and output tokens used',
    )
    try:
        self.tokens_histogram = self.meter.create_histogram(
            **tokens_histogram_kwargs,
            explicit_bucket_boundaries_advisory=TOKEN_HISTOGRAM_BOUNDARIES,
        )
    except TypeError:  # pragma: lax no cover
        # Older OTel/logfire versions don't support explicit_bucket_boundaries_advisory
        self.tokens_histogram = self.meter.create_histogram(
            **tokens_histogram_kwargs,  # pyright: ignore
        )
    self.cost_histogram = self.meter.create_histogram(
        'operation.cost',
        unit='{USD}',
        description='Monetary cost',
    )

```

#### messages_to_otel_events

```python
messages_to_otel_events(
    messages: list[ModelMessage],
    parameters: ModelRequestParameters | None = None,
) -> list[Event]

```

Convert a list of model messages to OpenTelemetry events.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `messages` | `list[ModelMessage]` | The messages to convert. | _required_ | | `parameters` | `ModelRequestParameters | None` | The model request parameters. | `None` |

Returns:

| Type | Description | | --- | --- | | `list[Event]` | A list of OpenTelemetry events. |

Source code in `pydantic_ai_slim/pydantic_ai/models/instrumented.py`

```python
def messages_to_otel_events(
    self, messages: list[ModelMessage], parameters: ModelRequestParameters | None = None
) -> list[Event]:
    """Convert a list of model messages to OpenTelemetry events.

    Args:
        messages: The messages to convert.
        parameters: The model request parameters.

    Returns:
        A list of OpenTelemetry events.
    """
    events: list[Event] = []
    instructions = InstrumentedModel._get_instructions(messages, parameters)  # pyright: ignore [reportPrivateUsage]
    if instructions is not None:
        events.append(
            Event(
                'gen_ai.system.message',
                body={**({'content': instructions} if self.include_content else {}), 'role': 'system'},
            )
        )

    for message_index, message in enumerate(messages):
        message_events: list[Event] = []
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if hasattr(part, 'otel_event'):
                    message_events.append(part.otel_event(self))
        elif isinstance(message, ModelResponse):  # pragma: no branch
            message_events = message.otel_events(self)
        for event in message_events:
            event.attributes = {
                'gen_ai.message.index': message_index,
                **(event.attributes or {}),
            }
        events.extend(message_events)

    for event in events:
        event.body = InstrumentedModel.serialize_any(event.body)
    return events

```
