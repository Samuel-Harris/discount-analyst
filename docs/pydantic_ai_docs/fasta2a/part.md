### Part

```python
Part = Annotated[
    Union[TextPart, FilePart, DataPart],
    Field(discriminator="kind"),
]

```

A fully formed piece of content exchanged between a client and a remote agent as part of a Message or an Artifact.

Each Part has its own content type and metadata.
