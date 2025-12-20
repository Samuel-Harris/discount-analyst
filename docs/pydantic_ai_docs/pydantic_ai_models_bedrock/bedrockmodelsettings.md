### BedrockModelSettings

Bases: `ModelSettings`

Settings for Bedrock models.

See [the Bedrock Converse API docs](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html#API_runtime_Converse_RequestSyntax) for a full list. See [the boto3 implementation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/converse.html) of the Bedrock Converse API.

Source code in `pydantic_ai_slim/pydantic_ai/models/bedrock.py`

```python
class BedrockModelSettings(ModelSettings, total=False):
    """Settings for Bedrock models.

    See [the Bedrock Converse API docs](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html#API_runtime_Converse_RequestSyntax) for a full list.
    See [the boto3 implementation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/converse.html) of the Bedrock Converse API.
    """

    # ALL FIELDS MUST BE `bedrock_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

    bedrock_guardrail_config: GuardrailConfigurationTypeDef
    """Content moderation and safety settings for Bedrock API requests.

    See more about it on <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailConfiguration.html>.
    """

    bedrock_performance_configuration: PerformanceConfigurationTypeDef
    """Performance optimization settings for model inference.

    See more about it on <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_PerformanceConfiguration.html>.
    """

    bedrock_request_metadata: dict[str, str]
    """Additional metadata to attach to Bedrock API requests.

    See more about it on <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html#API_runtime_Converse_RequestSyntax>.
    """

    bedrock_additional_model_response_fields_paths: list[str]
    """JSON paths to extract additional fields from model responses.

    See more about it on <https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html>.
    """

    bedrock_prompt_variables: Mapping[str, PromptVariableValuesTypeDef]
    """Variables for substitution into prompt templates.

    See more about it on <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_PromptVariableValues.html>.
    """

    bedrock_additional_model_requests_fields: Mapping[str, Any]
    """Additional model-specific parameters to include in requests.

    See more about it on <https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html>.
    """

```

#### bedrock_guardrail_config

```python
bedrock_guardrail_config: GuardrailConfigurationTypeDef

```

Content moderation and safety settings for Bedrock API requests.

See more about it on <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailConfiguration.html>.

#### bedrock_performance_configuration

```python
bedrock_performance_configuration: (
    PerformanceConfigurationTypeDef
)

```

Performance optimization settings for model inference.

See more about it on <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_PerformanceConfiguration.html>.

#### bedrock_request_metadata

```python
bedrock_request_metadata: dict[str, str]

```

Additional metadata to attach to Bedrock API requests.

See more about it on <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html#API_runtime_Converse_RequestSyntax>.

#### bedrock_additional_model_response_fields_paths

```python
bedrock_additional_model_response_fields_paths: list[str]

```

JSON paths to extract additional fields from model responses.

See more about it on <https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html>.

#### bedrock_prompt_variables

```python
bedrock_prompt_variables: Mapping[
    str, PromptVariableValuesTypeDef
]

```

Variables for substitution into prompt templates.

See more about it on <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_PromptVariableValues.html>.

#### bedrock_additional_model_requests_fields

```python
bedrock_additional_model_requests_fields: Mapping[str, Any]

```

Additional model-specific parameters to include in requests.

See more about it on <https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html>.
