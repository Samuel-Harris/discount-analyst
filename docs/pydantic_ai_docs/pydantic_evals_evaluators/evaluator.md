### Evaluator

Bases: `Generic[InputsT, OutputT, MetadataT]`

Base class for all evaluators.

Evaluators can assess the performance of a task in a variety of ways, as a function of the EvaluatorContext.

Subclasses must implement the `evaluate` method. Note it can be defined with either `def` or `async def`.

Example:

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ExactMatch(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output == ctx.expected_output

```

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

````python
@dataclass(repr=False)
class Evaluator(Generic[InputsT, OutputT, MetadataT], metaclass=_StrictABCMeta):
    """Base class for all evaluators.

    Evaluators can assess the performance of a task in a variety of ways, as a function of the EvaluatorContext.

    Subclasses must implement the `evaluate` method. Note it can be defined with either `def` or `async def`.

    Example:
    ```python
    from dataclasses import dataclass

    from pydantic_evals.evaluators import Evaluator, EvaluatorContext


    @dataclass
    class ExactMatch(Evaluator):
        def evaluate(self, ctx: EvaluatorContext) -> bool:
            return ctx.output == ctx.expected_output
    ```
    """

    __pydantic_config__ = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def get_serialization_name(cls) -> str:
        """Return the 'name' of this Evaluator to use during serialization.

        Returns:
            The name of the Evaluator, which is typically the class name.
        """
        return cls.__name__

    @classmethod
    @deprecated('`name` has been renamed, use `get_serialization_name` instead.')
    def name(cls) -> str:
        """`name` has been renamed, use `get_serialization_name` instead."""
        return cls.get_serialization_name()

    def get_default_evaluation_name(self) -> str:
        """Return the default name to use in reports for the output of this evaluator.

        By default, if the evaluator has an attribute called `evaluation_name` of type string, that will be used.
        Otherwise, the serialization name of the evaluator (which is usually the class name) will be used.

        This can be overridden to get a more descriptive name in evaluation reports, e.g. using instance information.

        Note that evaluators that return a mapping of results will always use the keys of that mapping as the names
        of the associated evaluation results.
        """
        evaluation_name = getattr(self, 'evaluation_name', None)
        if isinstance(evaluation_name, str):
            # If the evaluator has an attribute `name` of type string, use that
            return evaluation_name

        return self.get_serialization_name()

    @abstractmethod
    def evaluate(
        self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]
    ) -> EvaluatorOutput | Awaitable[EvaluatorOutput]:  # pragma: no cover
        """Evaluate the task output in the given context.

        This is the main evaluation method that subclasses must implement. It can be either synchronous
        or asynchronous, returning either an EvaluatorOutput directly or an Awaitable[EvaluatorOutput].

        Args:
            ctx: The context containing the inputs, outputs, and metadata for evaluation.

        Returns:
            The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
            of evaluation names to either of those. Can be returned either synchronously or as an
            awaitable for asynchronous evaluation.
        """
        raise NotImplementedError('You must implement `evaluate`.')

    def evaluate_sync(self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]) -> EvaluatorOutput:
        """Run the evaluator synchronously, handling both sync and async implementations.

        This method ensures synchronous execution by running any async evaluate implementation
        to completion using run_until_complete.

        Args:
            ctx: The context containing the inputs, outputs, and metadata for evaluation.

        Returns:
            The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
            of evaluation names to either of those.
        """
        output = self.evaluate(ctx)
        if inspect.iscoroutine(output):  # pragma: no cover
            return get_event_loop().run_until_complete(output)
        else:
            return cast(EvaluatorOutput, output)

    async def evaluate_async(self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]) -> EvaluatorOutput:
        """Run the evaluator asynchronously, handling both sync and async implementations.

        This method ensures asynchronous execution by properly awaiting any async evaluate
        implementation. For synchronous implementations, it returns the result directly.

        Args:
            ctx: The context containing the inputs, outputs, and metadata for evaluation.

        Returns:
            The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
            of evaluation names to either of those.
        """
        # Note: If self.evaluate is synchronous, but you need to prevent this from blocking, override this method with:
        # return await anyio.to_thread.run_sync(self.evaluate, ctx)
        output = self.evaluate(ctx)
        if inspect.iscoroutine(output):
            return await output
        else:
            return cast(EvaluatorOutput, output)

    @model_serializer(mode='plain')
    def serialize(self, info: SerializationInfo) -> Any:
        """Serialize this Evaluator to a JSON-serializable form.

        Returns:
            A JSON-serializable representation of this evaluator as an EvaluatorSpec.
        """
        return to_jsonable_python(
            self.as_spec(),
            context=info.context,
            serialize_unknown=True,
        )

    def as_spec(self) -> EvaluatorSpec:
        raw_arguments = self.build_serialization_arguments()

        arguments: None | tuple[Any,] | dict[str, Any]
        if len(raw_arguments) == 0:
            arguments = None
        elif len(raw_arguments) == 1:
            arguments = (next(iter(raw_arguments.values())),)
        else:
            arguments = raw_arguments

        return EvaluatorSpec(name=self.get_serialization_name(), arguments=arguments)

    def build_serialization_arguments(self) -> dict[str, Any]:
        """Build the arguments for serialization.

        Evaluators are serialized for inclusion as the "source" in an `EvaluationResult`.
        If you want to modify how the evaluator is serialized for that or other purposes, you can override this method.

        Returns:
            A dictionary of arguments to be used during serialization.
        """
        raw_arguments: dict[str, Any] = {}
        for field in fields(self):
            value = getattr(self, field.name)
            # always exclude defaults:
            if field.default is not MISSING:
                if value == field.default:
                    continue
            if field.default_factory is not MISSING:
                if value == field.default_factory():  # pragma: no branch
                    continue
            raw_arguments[field.name] = value
        return raw_arguments

    __repr__ = _utils.dataclasses_no_defaults_repr

````

#### get_serialization_name

```python
get_serialization_name() -> str

```

Return the 'name' of this Evaluator to use during serialization.

Returns:

| Type | Description | | --- | --- | | `str` | The name of the Evaluator, which is typically the class name. |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@classmethod
def get_serialization_name(cls) -> str:
    """Return the 'name' of this Evaluator to use during serialization.

    Returns:
        The name of the Evaluator, which is typically the class name.
    """
    return cls.__name__

```

#### name

```python
name() -> str

```

Deprecated

`name` has been renamed, use `get_serialization_name` instead.

`name` has been renamed, use `get_serialization_name` instead.

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@classmethod
@deprecated('`name` has been renamed, use `get_serialization_name` instead.')
def name(cls) -> str:
    """`name` has been renamed, use `get_serialization_name` instead."""
    return cls.get_serialization_name()

```

#### get_default_evaluation_name

```python
get_default_evaluation_name() -> str

```

Return the default name to use in reports for the output of this evaluator.

By default, if the evaluator has an attribute called `evaluation_name` of type string, that will be used. Otherwise, the serialization name of the evaluator (which is usually the class name) will be used.

This can be overridden to get a more descriptive name in evaluation reports, e.g. using instance information.

Note that evaluators that return a mapping of results will always use the keys of that mapping as the names of the associated evaluation results.

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
def get_default_evaluation_name(self) -> str:
    """Return the default name to use in reports for the output of this evaluator.

    By default, if the evaluator has an attribute called `evaluation_name` of type string, that will be used.
    Otherwise, the serialization name of the evaluator (which is usually the class name) will be used.

    This can be overridden to get a more descriptive name in evaluation reports, e.g. using instance information.

    Note that evaluators that return a mapping of results will always use the keys of that mapping as the names
    of the associated evaluation results.
    """
    evaluation_name = getattr(self, 'evaluation_name', None)
    if isinstance(evaluation_name, str):
        # If the evaluator has an attribute `name` of type string, use that
        return evaluation_name

    return self.get_serialization_name()

```

#### evaluate

```python
evaluate(
    ctx: EvaluatorContext[InputsT, OutputT, MetadataT],
) -> EvaluatorOutput | Awaitable[EvaluatorOutput]

```

Evaluate the task output in the given context.

This is the main evaluation method that subclasses must implement. It can be either synchronous or asynchronous, returning either an EvaluatorOutput directly or an Awaitable[EvaluatorOutput].

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `ctx` | `EvaluatorContext[InputsT, OutputT, MetadataT]` | The context containing the inputs, outputs, and metadata for evaluation. | _required_ |

Returns:

| Type | Description | | --- | --- | | `EvaluatorOutput | Awaitable[EvaluatorOutput]` | The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping | | `EvaluatorOutput | Awaitable[EvaluatorOutput]` | of evaluation names to either of those. Can be returned either synchronously or as an | | `EvaluatorOutput | Awaitable[EvaluatorOutput]` | awaitable for asynchronous evaluation. |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@abstractmethod
def evaluate(
    self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]
) -> EvaluatorOutput | Awaitable[EvaluatorOutput]:  # pragma: no cover
    """Evaluate the task output in the given context.

    This is the main evaluation method that subclasses must implement. It can be either synchronous
    or asynchronous, returning either an EvaluatorOutput directly or an Awaitable[EvaluatorOutput].

    Args:
        ctx: The context containing the inputs, outputs, and metadata for evaluation.

    Returns:
        The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
        of evaluation names to either of those. Can be returned either synchronously or as an
        awaitable for asynchronous evaluation.
    """
    raise NotImplementedError('You must implement `evaluate`.')

```

#### evaluate_sync

```python
evaluate_sync(
    ctx: EvaluatorContext[InputsT, OutputT, MetadataT],
) -> EvaluatorOutput

```

Run the evaluator synchronously, handling both sync and async implementations.

This method ensures synchronous execution by running any async evaluate implementation to completion using run_until_complete.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `ctx` | `EvaluatorContext[InputsT, OutputT, MetadataT]` | The context containing the inputs, outputs, and metadata for evaluation. | _required_ |

Returns:

| Type | Description | | --- | --- | | `EvaluatorOutput` | The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping | | `EvaluatorOutput` | of evaluation names to either of those. |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
def evaluate_sync(self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]) -> EvaluatorOutput:
    """Run the evaluator synchronously, handling both sync and async implementations.

    This method ensures synchronous execution by running any async evaluate implementation
    to completion using run_until_complete.

    Args:
        ctx: The context containing the inputs, outputs, and metadata for evaluation.

    Returns:
        The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
        of evaluation names to either of those.
    """
    output = self.evaluate(ctx)
    if inspect.iscoroutine(output):  # pragma: no cover
        return get_event_loop().run_until_complete(output)
    else:
        return cast(EvaluatorOutput, output)

```

#### evaluate_async

```python
evaluate_async(
    ctx: EvaluatorContext[InputsT, OutputT, MetadataT],
) -> EvaluatorOutput

```

Run the evaluator asynchronously, handling both sync and async implementations.

This method ensures asynchronous execution by properly awaiting any async evaluate implementation. For synchronous implementations, it returns the result directly.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `ctx` | `EvaluatorContext[InputsT, OutputT, MetadataT]` | The context containing the inputs, outputs, and metadata for evaluation. | _required_ |

Returns:

| Type | Description | | --- | --- | | `EvaluatorOutput` | The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping | | `EvaluatorOutput` | of evaluation names to either of those. |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
async def evaluate_async(self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]) -> EvaluatorOutput:
    """Run the evaluator asynchronously, handling both sync and async implementations.

    This method ensures asynchronous execution by properly awaiting any async evaluate
    implementation. For synchronous implementations, it returns the result directly.

    Args:
        ctx: The context containing the inputs, outputs, and metadata for evaluation.

    Returns:
        The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
        of evaluation names to either of those.
    """
    # Note: If self.evaluate is synchronous, but you need to prevent this from blocking, override this method with:
    # return await anyio.to_thread.run_sync(self.evaluate, ctx)
    output = self.evaluate(ctx)
    if inspect.iscoroutine(output):
        return await output
    else:
        return cast(EvaluatorOutput, output)

```

#### serialize

```python
serialize(info: SerializationInfo) -> Any

```

Serialize this Evaluator to a JSON-serializable form.

Returns:

| Type | Description | | --- | --- | | `Any` | A JSON-serializable representation of this evaluator as an EvaluatorSpec. |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@model_serializer(mode='plain')
def serialize(self, info: SerializationInfo) -> Any:
    """Serialize this Evaluator to a JSON-serializable form.

    Returns:
        A JSON-serializable representation of this evaluator as an EvaluatorSpec.
    """
    return to_jsonable_python(
        self.as_spec(),
        context=info.context,
        serialize_unknown=True,
    )

```

#### build_serialization_arguments

```python
build_serialization_arguments() -> dict[str, Any]

```

Build the arguments for serialization.

Evaluators are serialized for inclusion as the "source" in an `EvaluationResult`. If you want to modify how the evaluator is serialized for that or other purposes, you can override this method.

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | A dictionary of arguments to be used during serialization. |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
def build_serialization_arguments(self) -> dict[str, Any]:
    """Build the arguments for serialization.

    Evaluators are serialized for inclusion as the "source" in an `EvaluationResult`.
    If you want to modify how the evaluator is serialized for that or other purposes, you can override this method.

    Returns:
        A dictionary of arguments to be used during serialization.
    """
    raw_arguments: dict[str, Any] = {}
    for field in fields(self):
        value = getattr(self, field.name)
        # always exclude defaults:
        if field.default is not MISSING:
            if value == field.default:
                continue
        if field.default_factory is not MISSING:
            if value == field.default_factory():  # pragma: no branch
                continue
        raw_arguments[field.name] = value
    return raw_arguments

```
