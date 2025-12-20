### ToolOutput

Bases: `Generic[OutputDataT]`

Marker class to use a tool for output and optionally customize the tool.

Example: tool_output.py

```python
from pydantic import BaseModel

from pydantic_ai import Agent, ToolOutput


class Fruit(BaseModel):
    name: str
    color: str


class Vehicle(BaseModel):
    name: str
    wheels: int


agent = Agent(
    'openai:gpt-4o',
    output_type=[
        ToolOutput(Fruit, name='return_fruit'),
        ToolOutput(Vehicle, name='return_vehicle'),
    ],
)
result = agent.run_sync('What is a banana?')
print(repr(result.output))
#> Fruit(name='banana', color='yellow')

```

Source code in `pydantic_ai_slim/pydantic_ai/output.py`

````python
@dataclass(init=False)
class ToolOutput(Generic[OutputDataT]):
    """Marker class to use a tool for output and optionally customize the tool.

    Example:
    ```python {title="tool_output.py"}
    from pydantic import BaseModel

    from pydantic_ai import Agent, ToolOutput


    class Fruit(BaseModel):
        name: str
        color: str


    class Vehicle(BaseModel):
        name: str
        wheels: int


    agent = Agent(
        'openai:gpt-4o',
        output_type=[
            ToolOutput(Fruit, name='return_fruit'),
            ToolOutput(Vehicle, name='return_vehicle'),
        ],
    )
    result = agent.run_sync('What is a banana?')
    print(repr(result.output))
    #> Fruit(name='banana', color='yellow')
    ```
    """

    output: OutputTypeOrFunction[OutputDataT]
    """An output type or function."""
    name: str | None
    """The name of the tool that will be passed to the model. If not specified and only one output is provided, `final_result` will be used. If multiple outputs are provided, the name of the output type or function will be added to the tool name."""
    description: str | None
    """The description of the tool that will be passed to the model. If not specified, the docstring of the output type or function will be used."""
    max_retries: int | None
    """The maximum number of retries for the tool."""
    strict: bool | None
    """Whether to use strict mode for the tool."""

    def __init__(
        self,
        type_: OutputTypeOrFunction[OutputDataT],
        *,
        name: str | None = None,
        description: str | None = None,
        max_retries: int | None = None,
        strict: bool | None = None,
    ):
        self.output = type_
        self.name = name
        self.description = description
        self.max_retries = max_retries
        self.strict = strict

````

#### output

```python
output: OutputTypeOrFunction[OutputDataT] = type_

```

An output type or function.

#### name

```python
name: str | None = name

```

The name of the tool that will be passed to the model. If not specified and only one output is provided, `final_result` will be used. If multiple outputs are provided, the name of the output type or function will be added to the tool name.

#### description

```python
description: str | None = description

```

The description of the tool that will be passed to the model. If not specified, the docstring of the output type or function will be used.

#### max_retries

```python
max_retries: int | None = max_retries

```

The maximum number of retries for the tool.

#### strict

```python
strict: bool | None = strict

```

Whether to use strict mode for the tool.
