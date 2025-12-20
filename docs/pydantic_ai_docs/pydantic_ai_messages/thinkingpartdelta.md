### ThinkingPartDelta

A partial update (delta) for a `ThinkingPart` to append new thinking content.

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
@dataclass(repr=False, kw_only=True)
class ThinkingPartDelta:
    """A partial update (delta) for a `ThinkingPart` to append new thinking content."""

    content_delta: str | None = None
    """The incremental thinking content to add to the existing `ThinkingPart` content."""

    signature_delta: str | None = None
    """Optional signature delta.

    Note this is never treated as a delta â€” it can replace None.
    """

    provider_name: str | None = None
    """Optional provider name for the thinking part.

    Signatures are only sent back to the same provider.
    """

    provider_details: ProviderDetailsDelta = None
    """Additional data returned by the provider that can't be mapped to standard fields.

    Can be a dict to merge with existing details, or a callable that takes
    the existing details and returns updated details.

    This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically."""

    part_delta_kind: Literal['thinking'] = 'thinking'
    """Part delta type identifier, used as a discriminator."""

    @overload
    def apply(self, part: ModelResponsePart) -> ThinkingPart: ...

    @overload
    def apply(self, part: ModelResponsePart | ThinkingPartDelta) -> ThinkingPart | ThinkingPartDelta: ...

    def apply(self, part: ModelResponsePart | ThinkingPartDelta) -> ThinkingPart | ThinkingPartDelta:
        """Apply this thinking delta to an existing `ThinkingPart`.

        Args:
            part: The existing model response part, which must be a `ThinkingPart`.

        Returns:
            A new `ThinkingPart` with updated thinking content.

        Raises:
            ValueError: If `part` is not a `ThinkingPart`.
        """
        if isinstance(part, ThinkingPart):
            new_content = part.content + self.content_delta if self.content_delta else part.content
            new_signature = self.signature_delta if self.signature_delta is not None else part.signature
            new_provider_name = self.provider_name if self.provider_name is not None else part.provider_name
            # Resolve callable provider_details if needed
            resolved_details = (
                self.provider_details(part.provider_details)
                if callable(self.provider_details)
                else self.provider_details
            )
            new_provider_details = {**(part.provider_details or {}), **(resolved_details or {})} or None
            return replace(
                part,
                content=new_content,
                signature=new_signature,
                provider_name=new_provider_name,
                provider_details=new_provider_details,
            )
        elif isinstance(part, ThinkingPartDelta):
            if self.content_delta is None and self.signature_delta is None:
                raise ValueError('Cannot apply ThinkingPartDelta with no content or signature')
            if self.content_delta is not None:
                part = replace(part, content_delta=(part.content_delta or '') + self.content_delta)
            if self.signature_delta is not None:
                part = replace(part, signature_delta=self.signature_delta)
            if self.provider_name is not None:
                part = replace(part, provider_name=self.provider_name)
            if self.provider_details is not None:
                if callable(self.provider_details):
                    if callable(part.provider_details):
                        existing_fn = part.provider_details
                        new_fn = self.provider_details

                        def chained_both(d: dict[str, Any] | None) -> dict[str, Any]:
                            return new_fn(existing_fn(d))

                        part = replace(part, provider_details=chained_both)
                    else:
                        part = replace(part, provider_details=self.provider_details)  # pragma: no cover
                elif callable(part.provider_details):
                    existing_fn = part.provider_details
                    new_dict = self.provider_details

                    def chained_dict(d: dict[str, Any] | None) -> dict[str, Any]:
                        return {**existing_fn(d), **new_dict}

                    part = replace(part, provider_details=chained_dict)
                else:
                    existing = part.provider_details if isinstance(part.provider_details, dict) else {}
                    part = replace(part, provider_details={**existing, **self.provider_details})
            return part
        raise ValueError(  # pragma: no cover
            f'Cannot apply ThinkingPartDeltas to non-ThinkingParts or non-ThinkingPartDeltas ({part=}, {self=})'
        )

    __repr__ = _utils.dataclasses_no_defaults_repr

```

#### content_delta

```python
content_delta: str | None = None

```

The incremental thinking content to add to the existing `ThinkingPart` content.

#### signature_delta

```python
signature_delta: str | None = None

```

Optional signature delta.

Note this is never treated as a delta â€” it can replace None.

#### provider_name

```python
provider_name: str | None = None

```

Optional provider name for the thinking part.

Signatures are only sent back to the same provider.

#### provider_details

```python
provider_details: ProviderDetailsDelta = None

```

Additional data returned by the provider that can't be mapped to standard fields.

Can be a dict to merge with existing details, or a callable that takes the existing details and returns updated details.

This is used for data that is required to be sent back to APIs, as well as data users may want to access programmatically.

#### part_delta_kind

```python
part_delta_kind: Literal['thinking'] = 'thinking'

```

Part delta type identifier, used as a discriminator.

#### apply

```python
apply(part: ModelResponsePart) -> ThinkingPart

```

```python
apply(
    part: ModelResponsePart | ThinkingPartDelta,
) -> ThinkingPart | ThinkingPartDelta

```

```python
apply(
    part: ModelResponsePart | ThinkingPartDelta,
) -> ThinkingPart | ThinkingPartDelta

```

Apply this thinking delta to an existing `ThinkingPart`.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `part` | `ModelResponsePart | ThinkingPartDelta` | The existing model response part, which must be a ThinkingPart. | _required_ |

Returns:

| Type | Description | | --- | --- | | `ThinkingPart | ThinkingPartDelta` | A new ThinkingPart with updated thinking content. |

Raises:

| Type | Description | | --- | --- | | `ValueError` | If part is not a ThinkingPart. |

Source code in `pydantic_ai_slim/pydantic_ai/messages.py`

```python
def apply(self, part: ModelResponsePart | ThinkingPartDelta) -> ThinkingPart | ThinkingPartDelta:
    """Apply this thinking delta to an existing `ThinkingPart`.

    Args:
        part: The existing model response part, which must be a `ThinkingPart`.

    Returns:
        A new `ThinkingPart` with updated thinking content.

    Raises:
        ValueError: If `part` is not a `ThinkingPart`.
    """
    if isinstance(part, ThinkingPart):
        new_content = part.content + self.content_delta if self.content_delta else part.content
        new_signature = self.signature_delta if self.signature_delta is not None else part.signature
        new_provider_name = self.provider_name if self.provider_name is not None else part.provider_name
        # Resolve callable provider_details if needed
        resolved_details = (
            self.provider_details(part.provider_details)
            if callable(self.provider_details)
            else self.provider_details
        )
        new_provider_details = {**(part.provider_details or {}), **(resolved_details or {})} or None
        return replace(
            part,
            content=new_content,
            signature=new_signature,
            provider_name=new_provider_name,
            provider_details=new_provider_details,
        )
    elif isinstance(part, ThinkingPartDelta):
        if self.content_delta is None and self.signature_delta is None:
            raise ValueError('Cannot apply ThinkingPartDelta with no content or signature')
        if self.content_delta is not None:
            part = replace(part, content_delta=(part.content_delta or '') + self.content_delta)
        if self.signature_delta is not None:
            part = replace(part, signature_delta=self.signature_delta)
        if self.provider_name is not None:
            part = replace(part, provider_name=self.provider_name)
        if self.provider_details is not None:
            if callable(self.provider_details):
                if callable(part.provider_details):
                    existing_fn = part.provider_details
                    new_fn = self.provider_details

                    def chained_both(d: dict[str, Any] | None) -> dict[str, Any]:
                        return new_fn(existing_fn(d))

                    part = replace(part, provider_details=chained_both)
                else:
                    part = replace(part, provider_details=self.provider_details)  # pragma: no cover
            elif callable(part.provider_details):
                existing_fn = part.provider_details
                new_dict = self.provider_details

                def chained_dict(d: dict[str, Any] | None) -> dict[str, Any]:
                    return {**existing_fn(d), **new_dict}

                part = replace(part, provider_details=chained_dict)
            else:
                existing = part.provider_details if isinstance(part.provider_details, dict) else {}
                part = replace(part, provider_details={**existing, **self.provider_details})
        return part
    raise ValueError(  # pragma: no cover
        f'Cannot apply ThinkingPartDeltas to non-ThinkingParts or non-ThinkingPartDeltas ({part=}, {self=})'
    )

```
