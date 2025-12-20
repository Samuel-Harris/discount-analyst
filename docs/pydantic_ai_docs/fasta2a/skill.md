### Skill

Bases: `TypedDict`

Skills are a unit of capability that an agent can perform.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class Skill(TypedDict):
    """Skills are a unit of capability that an agent can perform."""

    id: str
    """A unique identifier for the skill."""

    name: str
    """Human readable name of the skill."""

    description: str
    """A human-readable description of the skill.

    It will be used by the client or a human as a hint to understand the skill.
    """

    tags: list[str]
    """Set of tag-words describing classes of capabilities for this specific skill.

    Examples: "cooking", "customer support", "billing".
    """

    examples: NotRequired[list[str]]
    """The set of example scenarios that the skill can perform.

    Will be used by the client as a hint to understand how the skill can be used. (e.g. "I need a recipe for bread")
    """

    input_modes: list[str]
    """Supported mime types for input data."""

    output_modes: list[str]
    """Supported mime types for output data."""

```

#### id

```python
id: str

```

A unique identifier for the skill.

#### name

```python
name: str

```

Human readable name of the skill.

#### description

```python
description: str

```

A human-readable description of the skill.

It will be used by the client or a human as a hint to understand the skill.

#### tags

```python
tags: list[str]

```

Set of tag-words describing classes of capabilities for this specific skill.

Examples: "cooking", "customer support", "billing".

#### examples

```python
examples: NotRequired[list[str]]

```

The set of example scenarios that the skill can perform.

Will be used by the client as a hint to understand how the skill can be used. (e.g. "I need a recipe for bread")

#### input_modes

```python
input_modes: list[str]

```

Supported mime types for input data.

#### output_modes

```python
output_modes: list[str]

```

Supported mime types for output data.
