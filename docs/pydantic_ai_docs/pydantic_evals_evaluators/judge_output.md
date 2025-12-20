### judge_output

```python
judge_output(
    output: Any,
    rubric: str,
    model: Model | KnownModelName | None = None,
    model_settings: ModelSettings | None = None,
) -> GradingOutput

```

Judge the output of a model based on a rubric.

If the model is not specified, a default model is used. The default model starts as 'openai:gpt-4o', but this can be changed using the `set_default_judge_model` function.

Source code in `pydantic_evals/pydantic_evals/evaluators/llm_as_a_judge.py`

```python
async def judge_output(
    output: Any,
    rubric: str,
    model: models.Model | models.KnownModelName | None = None,
    model_settings: ModelSettings | None = None,
) -> GradingOutput:
    """Judge the output of a model based on a rubric.

    If the model is not specified, a default model is used. The default model starts as 'openai:gpt-4o',
    but this can be changed using the `set_default_judge_model` function.
    """
    user_prompt = _build_prompt(output=output, rubric=rubric)
    return (
        await _judge_output_agent.run(user_prompt, model=model or _default_model, model_settings=model_settings)
    ).output

```
