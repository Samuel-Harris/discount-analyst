### PromptedOutput

Bases: `Generic[OutputDataT]`

Marker class to use a prompt to tell the model what to output and optionally customize the prompt.

Example: prompted_output.py

```python
from pydantic import BaseModel

from pydantic_ai import Agent, PromptedOutput

from tool_output import Vehicle


class Device(BaseModel):
    name: str
    kind: str


agent = Agent(
    'openai:gpt-4o',
    output_type=PromptedOutput(
        [Vehicle, Device],
        name='Vehicle or device',
        description='Return a vehicle or device.'
    ),
)
result = agent.run_sync('What is a MacBook?')
print(repr(result.output))
#> Device(name='MacBook', kind='laptop')

agent = Agent(
    'openai:gpt-4o',
    output_type=PromptedOutput(
        [Vehicle, Device],
        template='Gimme some JSON: {schema}'
    ),
)
result = agent.run_sync('What is a Ford Explorer?')
print(repr(result.output))
#> Vehicle(name='Ford Explorer', wheels=4)

```

Source code in `pydantic_ai_slim/pydantic_ai/output.py`

````python
@dataclass(init=False)
class PromptedOutput(Generic[OutputDataT]):
    """Marker class to use a prompt to tell the model what to output and optionally customize the prompt.

    Example:
    ```python {title="prompted_output.py" requires="tool_output.py"}
    from pydantic import BaseModel

    from pydantic_ai import Agent, PromptedOutput

    from tool_output import Vehicle


    class Device(BaseModel):
        name: str
        kind: str


    agent = Agent(
        'openai:gpt-4o',
        output_type=PromptedOutput(
            [Vehicle, Device],
            name='Vehicle or device',
            description='Return a vehicle or device.'
        ),
    )
    result = agent.run_sync('What is a MacBook?')
    print(repr(result.output))
    #> Device(name='MacBook', kind='laptop')

    agent = Agent(
        'openai:gpt-4o',
        output_type=PromptedOutput(
            [Vehicle, Device],
            template='Gimme some JSON: {schema}'
        ),
    )
    result = agent.run_sync('What is a Ford Explorer?')
    print(repr(result.output))
    #> Vehicle(name='Ford Explorer', wheels=4)
    ```
    """

    outputs: OutputTypeOrFunction[OutputDataT] | Sequence[OutputTypeOrFunction[OutputDataT]]
    """The output types or functions."""
    name: str | None
    """The name of the structured output that will be passed to the model. If not specified and only one output is provided, the name of the output type or function will be used."""
    description: str | None
    """The description that will be passed to the model. If not specified and only one output is provided, the docstring of the output type or function will be used."""
    template: str | None
    """Template for the prompt passed to the model.
    The '{schema}' placeholder will be replaced with the output JSON schema.
    If not specified, the default template specified on the model's profile will be used.
    """

    def __init__(
        self,
        outputs: OutputTypeOrFunction[OutputDataT] | Sequence[OutputTypeOrFunction[OutputDataT]],
        *,
        name: str | None = None,
        description: str | None = None,
        template: str | None = None,
    ):
        self.outputs = outputs
        self.name = name
        self.description = description
        self.template = template

````

#### outputs

```python
outputs: (
    OutputTypeOrFunction[OutputDataT]
    | Sequence[OutputTypeOrFunction[OutputDataT]]
) = outputs

```

The output types or functions.

#### name

```python
name: str | None = name

```

The name of the structured output that will be passed to the model. If not specified and only one output is provided, the name of the output type or function will be used.

#### description

```python
description: str | None = description

```

The description that will be passed to the model. If not specified and only one output is provided, the docstring of the output type or function will be used.

#### template

```python
template: str | None = template

```

Template for the prompt passed to the model. The '{schema}' placeholder will be replaced with the output JSON schema. If not specified, the default template specified on the model's profile will be used.
