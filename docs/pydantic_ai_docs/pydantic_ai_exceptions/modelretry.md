### ModelRetry

Bases: `Exception`

Exception to raise when a tool function should be retried.

The agent will return the message to the model and ask it to try calling the function/tool again.

Source code in `pydantic_ai_slim/pydantic_ai/exceptions.py`

```python
class ModelRetry(Exception):
    """Exception to raise when a tool function should be retried.

    The agent will return the message to the model and ask it to try calling the function/tool again.
    """

    message: str
    """The message to return to the model."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and other.message == self.message

    def __hash__(self) -> int:
        return hash((self.__class__, self.message))

    @classmethod
    def __get_pydantic_core_schema__(cls, _: Any, __: Any) -> core_schema.CoreSchema:
        """Pydantic core schema to allow `ModelRetry` to be (de)serialized."""
        schema = core_schema.typed_dict_schema(
            {
                'message': core_schema.typed_dict_field(core_schema.str_schema()),
                'kind': core_schema.typed_dict_field(core_schema.literal_schema(['model-retry'])),
            }
        )
        return core_schema.no_info_after_validator_function(
            lambda dct: ModelRetry(dct['message']),
            schema,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: {'message': x.message, 'kind': 'model-retry'},
                return_schema=schema,
            ),
        )

```

#### message

```python
message: str = message

```

The message to return to the model.

#### **get_pydantic_core_schema**

```python
__get_pydantic_core_schema__(_: Any, __: Any) -> CoreSchema

```

Pydantic core schema to allow `ModelRetry` to be (de)serialized.

Source code in `pydantic_ai_slim/pydantic_ai/exceptions.py`

```python
@classmethod
def __get_pydantic_core_schema__(cls, _: Any, __: Any) -> core_schema.CoreSchema:
    """Pydantic core schema to allow `ModelRetry` to be (de)serialized."""
    schema = core_schema.typed_dict_schema(
        {
            'message': core_schema.typed_dict_field(core_schema.str_schema()),
            'kind': core_schema.typed_dict_field(core_schema.literal_schema(['model-retry'])),
        }
    )
    return core_schema.no_info_after_validator_function(
        lambda dct: ModelRetry(dct['message']),
        schema,
        serialization=core_schema.plain_serializer_function_ser_schema(
            lambda x: {'message': x.message, 'kind': 'model-retry'},
            return_schema=schema,
        ),
    )

```
