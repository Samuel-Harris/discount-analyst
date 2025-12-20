### Validation context

Some validation relies on an extra Pydantic [context](https://docs.pydantic.dev/latest/concepts/validators/#validation-context) object. You can pass such an object to an `Agent` at definition-time via its validation_context parameter. It will be used in the validation of both structured outputs and [tool arguments](../tools-advanced/#tool-retries).

This validation context can be either:

- the context object itself (`Any`), used as-is to validate outputs, or
- a function that takes the RunContext and returns a context object (`Any`). This function will be called automatically before each validation, allowing you to build a dynamic validation context.

Don't confuse this _validation_ context with the _LLM_ context

This Pydantic validation context object is only used internally by Pydantic AI for tool arg and output validation. In particular, it is **not** included in the prompts or messages sent to the language model.

validation_context.py

```python
from dataclasses import dataclass

from pydantic import BaseModel, ValidationInfo, field_validator

from pydantic_ai import Agent


class Value(BaseModel):
    x: int

    @field_validator('x')
    def increment_value(cls, value: int, info: ValidationInfo):
        return value + (info.context or 0)


agent = Agent(
    'google-gla:gemini-2.5-flash',
    output_type=Value,
    validation_context=10,
)
result = agent.run_sync('Give me a value of 5.')
print(repr(result.output))  # 5 from the model + 10 from the validation context
#> Value(x=15)


@dataclass
class Deps:
    increment: int


agent = Agent(
    'google-gla:gemini-2.5-flash',
    output_type=Value,
    deps_type=Deps,
    validation_context=lambda ctx: ctx.deps.increment,
)
result = agent.run_sync('Give me a value of 5.', deps=Deps(increment=10))
print(repr(result.output))  # 5 from the model + 10 from the validation context
#> Value(x=15)

```

_(This example is complete, it can be run "as is")_
