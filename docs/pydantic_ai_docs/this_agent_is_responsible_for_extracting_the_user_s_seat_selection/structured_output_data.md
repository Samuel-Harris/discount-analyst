## Structured output data

The Agent class constructor takes an `output_type` argument that takes one or more types or [output functions](#output-functions). It supports simple scalar types, list and dict types (including `TypedDict`s and [`StructuredDict`s](#structured-dict)), dataclasses and Pydantic models, as well as type unions -- generally everything supported as type hints in a Pydantic model. You can also pass a list of multiple choices.

By default, Pydantic AI leverages the model's tool calling capability to make it return structured data. When multiple output types are specified (in a union or list), each member is registered with the model as a separate output tool in order to reduce the complexity of the schema and maximise the chances a model will respond correctly. This has been shown to work well across a wide range of models. If you'd like to change the names of the output tools, use a model's native structured output feature, or pass the output schema to the model in its [instructions](../agents/#instructions), you can use an [output mode](#output-modes) marker class.

When no output type is specified, or when `str` is among the output types, any plain text response from the model will be used as the output data. If `str` is not among the output types, the model is forced to return structured data or call an output function.

If the output type schema is not of type `"object"` (e.g. it's `int` or `list[int]`), the output type is wrapped in a single element object, so the schema of all tools registered with the model are object schemas.

Structured outputs (like tools) use Pydantic to build the JSON schema used for the tool, and to validate the data returned by the model.

Type checking considerations

The Agent class is generic in its output type, and this type is carried through to `AgentRunResult.output` and `StreamedRunResult.output` so that your IDE or static type checker can warn you when your code doesn't properly take into account all the possible values those outputs could have.

Static type checkers like pyright and mypy will do their best to infer the agent's output type from the `output_type` you've specified, but they're not always able to do so correctly when you provide functions or multiple types in a union or list, even though Pydantic AI will behave correctly. When this happens, your type checker will complain even when you're confident you've passed a valid `output_type`, and you'll need to help the type checker by explicitly specifying the generic parameters on the `Agent` constructor. This is shown in the second example below and the output functions example further down.

Specifically, there are three valid uses of `output_type` where you'll need to do this:

1. When using a union of types, e.g. `output_type=Foo | Bar`. Until [PEP-747](https://peps.python.org/pep-0747/) "Annotating Type Forms" lands in Python 3.15, type checkers do not consider these a valid value for `output_type`. In addition to the generic parameters on the `Agent` constructor, you'll need to add `# type: ignore` to the line that passes the union to `output_type`. Alternatively, you can use a list: `output_type=[Foo, Bar]`.
1. With mypy: When using a list, as a functionally equivalent alternative to a union, or because you're passing in [output functions](#output-functions). Pyright does handle this correctly, and we've filed [an issue](https://github.com/python/mypy/issues/19142) with mypy to try and get this fixed.
1. With mypy: when using an async output function. Pyright does handle this correctly, and we've filed [an issue](https://github.com/python/mypy/issues/19143) with mypy to try and get this fixed.

Here's an example of returning either text or structured data:

[Learn about Gateway](../gateway) box_or_error.py

```python
from pydantic import BaseModel

from pydantic_ai import Agent


class Box(BaseModel):
    width: int
    height: int
    depth: int
    units: str


agent = Agent(
    'gateway/openai:gpt-5-mini',
    output_type=[Box, str], # (1)!
    system_prompt=(
        "Extract me the dimensions of a box, "
        "if you can't extract all data, ask the user to try again."
    ),
)

result = agent.run_sync('The box is 10x20x30')
print(result.output)
#> Please provide the units for the dimensions (e.g., cm, in, m).

result = agent.run_sync('The box is 10x20x30 cm')
print(result.output)
#> width=10 height=20 depth=30 units='cm'

```

1. This could also have been a union: `output_type=Box | str`. However, as explained in the "Type checking considerations" section above, that would've required explicitly specifying the generic parameters on the `Agent` constructor and adding `# type: ignore` to this line in order to be type checked correctly.

box_or_error.py

```python
from pydantic import BaseModel

from pydantic_ai import Agent


class Box(BaseModel):
    width: int
    height: int
    depth: int
    units: str


agent = Agent(
    'openai:gpt-5-mini',
    output_type=[Box, str], # (1)!
    system_prompt=(
        "Extract me the dimensions of a box, "
        "if you can't extract all data, ask the user to try again."
    ),
)

result = agent.run_sync('The box is 10x20x30')
print(result.output)
#> Please provide the units for the dimensions (e.g., cm, in, m).

result = agent.run_sync('The box is 10x20x30 cm')
print(result.output)
#> width=10 height=20 depth=30 units='cm'

```

1. This could also have been a union: `output_type=Box | str`. However, as explained in the "Type checking considerations" section above, that would've required explicitly specifying the generic parameters on the `Agent` constructor and adding `# type: ignore` to this line in order to be type checked correctly.

_(This example is complete, it can be run "as is")_

Here's an example of using a union return type, which will register multiple output tools and wrap non-object schemas in an object:

colors_or_sizes.py

```python
from pydantic_ai import Agent

agent = Agent[None, list[str] | list[int]](
    'openai:gpt-5-mini',
    output_type=list[str] | list[int],  # type: ignore # (1)!
    system_prompt='Extract either colors or sizes from the shapes provided.',
)

result = agent.run_sync('red square, blue circle, green triangle')
print(result.output)
#> ['red', 'blue', 'green']

result = agent.run_sync('square size 10, circle size 20, triangle size 30')
print(result.output)
#> [10, 20, 30]

```

1. As explained in the "Type checking considerations" section above, using a union rather than a list requires explicitly specifying the generic parameters on the `Agent` constructor and adding `# type: ignore` to this line in order to be type checked correctly.

_(This example is complete, it can be run "as is")_
