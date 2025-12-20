result_sync = agent.run_sync(
    'What is the capital of Italy?',
    model_settings=ModelSettings(temperature=0.0)  # Final temperature: 0.0
)
print(result_sync.output)
#> The capital of Italy is Rome.

```

The final request uses `temperature=0.0` (run-time), `max_tokens=500` (from model), demonstrating how settings merge with run-time taking precedence.

Model Settings Support

Model-level settings are supported by all concrete model implementations (OpenAI, Anthropic, Google, etc.). Wrapper models like [`FallbackModel`](../models/overview/#fallback-model), WrapperModel, and InstrumentedModel don't have their own settings - they use the settings of their underlying models.
