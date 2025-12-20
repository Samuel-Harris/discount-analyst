### instrument_model

```python
instrument_model(
    model: Model, instrument: InstrumentationSettings | bool
) -> Model

```

Instrument a model with OpenTelemetry/logfire.

Source code in `pydantic_ai_slim/pydantic_ai/models/instrumented.py`

```python
def instrument_model(model: Model, instrument: InstrumentationSettings | bool) -> Model:
    """Instrument a model with OpenTelemetry/logfire."""
    if instrument and not isinstance(model, InstrumentedModel):
        if instrument is True:
            instrument = InstrumentationSettings()

        model = InstrumentedModel(model, instrument)

    return model

```
