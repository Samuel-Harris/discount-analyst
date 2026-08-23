"""Unwrap singleton envelopes around pydantic-ai ``final_result`` arguments."""

from functools import cache
from typing import cast

from pydantic import BaseModel, model_validator

SINGLETON_ENVELOPE_KEYS = frozenset({"payload", "data", "response", "result", "output"})


def unwrap_singleton_output_envelope(value: object) -> object:
    """Flatten ``{"payload": {…schema fields…}}`` (and similar) to the inner dict.

    Only a dict with exactly one of the known envelope keys whose value is itself a
    dict is unwrapped. Two-key dicts, non-dict inners, and already-flat objects are
    returned unchanged.
    """
    if not isinstance(value, dict):
        return value
    envelope = cast(dict[object, object], value)
    if len(envelope) != 1:
        return envelope
    key, inner = next(iter(envelope.items()))
    if not isinstance(key, str) or key not in SINGLETON_ENVELOPE_KEYS:
        return envelope
    if not isinstance(inner, dict):
        return envelope
    return cast(dict[object, object], inner)


def singleton_envelope_keys_for_prompt() -> str:
    return ", ".join(f"`{key}`" for key in sorted(SINGLETON_ENVELOPE_KEYS))


@cache
def unwrapping_output_type[OutT](output_type: type[OutT]) -> type[OutT]:
    """Stage model whose validation unwraps a singleton envelope first.

    ``ToolOutput(Annotated[Model, BeforeValidator(...)])`` is not model-like, so
    pydantic-ai wraps the JSON schema under ``response``. A private subclass keeps
    ``final_result`` parameters as the flat stage fields.
    """
    if not issubclass(output_type, BaseModel):
        return output_type

    class UnwrappingOutput(output_type):
        @model_validator(mode="before")
        @classmethod
        def unwrap_singleton_envelope(cls, value: object) -> object:
            return unwrap_singleton_output_envelope(value)

    UnwrappingOutput.__name__ = output_type.__name__
    UnwrappingOutput.__qualname__ = output_type.__qualname__
    UnwrappingOutput.__doc__ = output_type.__doc__
    UnwrappingOutput.__module__ = output_type.__module__
    return UnwrappingOutput  # type: ignore[return-value]
