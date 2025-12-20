### Artifact

Bases: `TypedDict`

Agents generate Artifacts as an end result of a Task.

Artifacts are immutable, can be named, and can have multiple parts. A streaming response can append parts to existing Artifacts.

A single Task can generate many Artifacts. For example, "create a webpage" could create separate HTML and image Artifacts.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/schema.py`

```python
@pydantic.with_config({'alias_generator': to_camel})
class Artifact(TypedDict):
    """Agents generate Artifacts as an end result of a Task.

    Artifacts are immutable, can be named, and can have multiple parts. A streaming response can append parts to
    existing Artifacts.

    A single Task can generate many Artifacts. For example, "create a webpage" could create separate HTML and image
    Artifacts.
    """

    artifact_id: str
    """Unique identifier for the artifact."""

    name: NotRequired[str]
    """The name of the artifact."""

    description: NotRequired[str]
    """A description of the artifact."""

    parts: list[Part]
    """The parts that make up the artifact."""

    metadata: NotRequired[dict[str, Any]]
    """Metadata about the artifact."""

    extensions: NotRequired[list[str]]
    """Array of extensions."""

    append: NotRequired[bool]
    """Whether to append this artifact to an existing one."""

    last_chunk: NotRequired[bool]
    """Whether this is the last chunk of the artifact."""

```

#### artifact_id

```python
artifact_id: str

```

Unique identifier for the artifact.

#### name

```python
name: NotRequired[str]

```

The name of the artifact.

#### description

```python
description: NotRequired[str]

```

A description of the artifact.

#### parts

```python
parts: list[Part]

```

The parts that make up the artifact.

#### metadata

```python
metadata: NotRequired[dict[str, Any]]

```

Metadata about the artifact.

#### extensions

```python
extensions: NotRequired[list[str]]

```

Array of extensions.

#### append

```python
append: NotRequired[bool]

```

Whether to append this artifact to an existing one.

#### last_chunk

```python
last_chunk: NotRequired[bool]

```

Whether this is the last chunk of the artifact.
