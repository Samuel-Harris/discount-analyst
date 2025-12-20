### set_default_judge_model

```python
set_default_judge_model(
    model: Model | KnownModelName,
) -> None

```

Set the default model used for judging.

This model is used if `None` is passed to the `model` argument of `judge_output` and `judge_input_output`.

Source code in `pydantic_evals/pydantic_evals/evaluators/llm_as_a_judge.py`

```python
def set_default_judge_model(model: models.Model | models.KnownModelName) -> None:
    """Set the default model used for judging.

    This model is used if `None` is passed to the `model` argument of `judge_output` and `judge_input_output`.
    """
    global _default_model
    _default_model = model

```
