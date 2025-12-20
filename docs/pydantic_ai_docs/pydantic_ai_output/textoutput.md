### TextOutput

Bases: `Generic[OutputDataT]`

Marker class to use text output for an output function taking a string argument.

Example:

```python
from pydantic_ai import Agent, TextOutput


def split_into_words(text: str) -> list[str]:
    return text.split()


agent = Agent(
    'openai:gpt-4o',
    output_type=TextOutput(split_into_words),
)
result = agent.run_sync('Who was Albert Einstein?')
print(result.output)
#> ['Albert', 'Einstein', 'was', 'a', 'German-born', 'theoretical', 'physicist.']

```

Source code in `pydantic_ai_slim/pydantic_ai/output.py`

````python
@dataclass
class TextOutput(Generic[OutputDataT]):
    """Marker class to use text output for an output function taking a string argument.

    Example:
    ```python
    from pydantic_ai import Agent, TextOutput


    def split_into_words(text: str) -> list[str]:
        return text.split()


    agent = Agent(
        'openai:gpt-4o',
        output_type=TextOutput(split_into_words),
    )
    result = agent.run_sync('Who was Albert Einstein?')
    print(result.output)
    #> ['Albert', 'Einstein', 'was', 'a', 'German-born', 'theoretical', 'physicist.']
    ```
    """

    output_function: TextOutputFunc[OutputDataT]
    """The function that will be called to process the model's plain text output. The function must take a single string argument."""

````

#### output_function

```python
output_function: TextOutputFunc[OutputDataT]

```

The function that will be called to process the model's plain text output. The function must take a single string argument.
