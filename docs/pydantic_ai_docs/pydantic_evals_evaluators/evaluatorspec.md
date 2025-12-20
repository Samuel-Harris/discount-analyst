### EvaluatorSpec

Bases: `BaseModel`

The specification of an evaluator to be run.

This class is used to represent evaluators in a serializable format, supporting various short forms for convenience when defining evaluators in YAML or JSON dataset files.

In particular, each of the following forms is supported for specifying an evaluator with name `MyEvaluator`: _ `'MyEvaluator'` - Just the (string) name of the Evaluator subclass is used if its `__init__` takes no arguments _ `{'MyEvaluator': first_arg}` - A single argument is passed as the first positional argument to `MyEvaluator.__init__` \* `{'MyEvaluator': {k1: v1, k2: v2}}` - Multiple kwargs are passed to `MyEvaluator.__init__`

Source code in `pydantic_evals/pydantic_evals/evaluators/spec.py`

```python
class EvaluatorSpec(BaseModel):
    """The specification of an evaluator to be run.

    This class is used to represent evaluators in a serializable format, supporting various
    short forms for convenience when defining evaluators in YAML or JSON dataset files.

    In particular, each of the following forms is supported for specifying an evaluator with name `MyEvaluator`:
    * `'MyEvaluator'` - Just the (string) name of the Evaluator subclass is used if its `__init__` takes no arguments
    * `{'MyEvaluator': first_arg}` - A single argument is passed as the first positional argument to `MyEvaluator.__init__`
    * `{'MyEvaluator': {k1: v1, k2: v2}}` - Multiple kwargs are passed to `MyEvaluator.__init__`
    """

    name: str
    """The name of the evaluator class; should be the value returned by `EvaluatorClass.get_serialization_name()`"""

    arguments: None | tuple[Any] | dict[str, Any]
    """The arguments to pass to the evaluator's constructor.

    Can be None (no arguments), a tuple (a single positional argument), or a dict (keyword arguments).
    """

    @property
    def args(self) -> tuple[Any, ...]:
        """Get the positional arguments for the evaluator.

        Returns:
            A tuple of positional arguments if arguments is a tuple, otherwise an empty tuple.
        """
        if isinstance(self.arguments, tuple):
            return self.arguments
        return ()

    @property
    def kwargs(self) -> dict[str, Any]:
        """Get the keyword arguments for the evaluator.

        Returns:
            A dictionary of keyword arguments if arguments is a dict, otherwise an empty dict.
        """
        if isinstance(self.arguments, dict):
            return self.arguments
        return {}

    @model_validator(mode='wrap')
    @classmethod
    def deserialize(cls, value: Any, handler: ModelWrapValidatorHandler[EvaluatorSpec]) -> EvaluatorSpec:
        """Deserialize an EvaluatorSpec from various formats.

        This validator handles the various short forms of evaluator specifications,
        converting them to a consistent EvaluatorSpec instance.

        Args:
            value: The value to deserialize.
            handler: The validator handler.

        Returns:
            The deserialized EvaluatorSpec.

        Raises:
            ValidationError: If the value cannot be deserialized.
        """
        try:
            result = handler(value)
            return result
        except ValidationError as exc:
            try:
                deserialized = _SerializedEvaluatorSpec.model_validate(value)
            except ValidationError:
                raise exc  # raise the original error
            return deserialized.to_evaluator_spec()

    @model_serializer(mode='wrap')
    def serialize(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo) -> Any:
        """Serialize using the appropriate short-form if possible.

        Returns:
            The serialized evaluator specification, using the shortest form possible:
            - Just the name if there are no arguments
            - {name: first_arg} if there's a single positional argument
            - {name: {kwargs}} if there are multiple (keyword) arguments
        """
        if isinstance(info.context, dict) and info.context.get('use_short_form'):  # pyright: ignore[reportUnknownMemberType]
            if self.arguments is None:
                return self.name
            elif isinstance(self.arguments, tuple):
                return {self.name: self.arguments[0]}
            else:
                return {self.name: self.arguments}
        else:
            return handler(self)

```

#### name

```python
name: str

```

The name of the evaluator class; should be the value returned by `EvaluatorClass.get_serialization_name()`

#### arguments

```python
arguments: None | tuple[Any] | dict[str, Any]

```

The arguments to pass to the evaluator's constructor.

Can be None (no arguments), a tuple (a single positional argument), or a dict (keyword arguments).

#### args

```python
args: tuple[Any, ...]

```

Get the positional arguments for the evaluator.

Returns:

| Type | Description | | --- | --- | | `tuple[Any, ...]` | A tuple of positional arguments if arguments is a tuple, otherwise an empty tuple. |

#### kwargs

```python
kwargs: dict[str, Any]

```

Get the keyword arguments for the evaluator.

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | A dictionary of keyword arguments if arguments is a dict, otherwise an empty dict. |

#### deserialize

```python
deserialize(
    value: Any,
    handler: ModelWrapValidatorHandler[EvaluatorSpec],
) -> EvaluatorSpec

```

Deserialize an EvaluatorSpec from various formats.

This validator handles the various short forms of evaluator specifications, converting them to a consistent EvaluatorSpec instance.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `Any` | The value to deserialize. | _required_ | | `handler` | `ModelWrapValidatorHandler[EvaluatorSpec]` | The validator handler. | _required_ |

Returns:

| Type | Description | | --- | --- | | `EvaluatorSpec` | The deserialized EvaluatorSpec. |

Raises:

| Type | Description | | --- | --- | | `ValidationError` | If the value cannot be deserialized. |

Source code in `pydantic_evals/pydantic_evals/evaluators/spec.py`

```python
@model_validator(mode='wrap')
@classmethod
def deserialize(cls, value: Any, handler: ModelWrapValidatorHandler[EvaluatorSpec]) -> EvaluatorSpec:
    """Deserialize an EvaluatorSpec from various formats.

    This validator handles the various short forms of evaluator specifications,
    converting them to a consistent EvaluatorSpec instance.

    Args:
        value: The value to deserialize.
        handler: The validator handler.

    Returns:
        The deserialized EvaluatorSpec.

    Raises:
        ValidationError: If the value cannot be deserialized.
    """
    try:
        result = handler(value)
        return result
    except ValidationError as exc:
        try:
            deserialized = _SerializedEvaluatorSpec.model_validate(value)
        except ValidationError:
            raise exc  # raise the original error
        return deserialized.to_evaluator_spec()

```

#### serialize

```python
serialize(
    handler: SerializerFunctionWrapHandler,
    info: SerializationInfo,
) -> Any

```

Serialize using the appropriate short-form if possible.

Returns:

| Type | Description | | --- | --- | | `Any` | The serialized evaluator specification, using the shortest form possible: | | `Any` | Just the name if there are no arguments | | `Any` | {name: first_arg} if there's a single positional argument | | `Any` | {name: {kwargs}} if there are multiple (keyword) arguments |

Source code in `pydantic_evals/pydantic_evals/evaluators/spec.py`

```python
@model_serializer(mode='wrap')
def serialize(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo) -> Any:
    """Serialize using the appropriate short-form if possible.

    Returns:
        The serialized evaluator specification, using the shortest form possible:
        - Just the name if there are no arguments
        - {name: first_arg} if there's a single positional argument
        - {name: {kwargs}} if there are multiple (keyword) arguments
    """
    if isinstance(info.context, dict) and info.context.get('use_short_form'):  # pyright: ignore[reportUnknownMemberType]
        if self.arguments is None:
            return self.name
        elif isinstance(self.arguments, tuple):
            return {self.name: self.arguments[0]}
        else:
            return {self.name: self.arguments}
    else:
        return handler(self)

```
