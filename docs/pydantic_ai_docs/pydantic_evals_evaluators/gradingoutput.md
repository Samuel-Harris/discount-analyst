### GradingOutput

Bases: `BaseModel`

The output of a grading operation.

Source code in `pydantic_evals/pydantic_evals/evaluators/llm_as_a_judge.py`

```python
class GradingOutput(BaseModel, populate_by_name=True):
    """The output of a grading operation."""

    reason: str
    pass_: bool = Field(validation_alias='pass', serialization_alias='pass')
    score: float

```
