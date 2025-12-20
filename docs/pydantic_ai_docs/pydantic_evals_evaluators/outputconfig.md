### OutputConfig

Bases: `TypedDict`

Configuration for the score and assertion outputs of the LLMJudge evaluator.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
class OutputConfig(TypedDict, total=False):
    """Configuration for the score and assertion outputs of the LLMJudge evaluator."""

    evaluation_name: str
    include_reason: bool

```
