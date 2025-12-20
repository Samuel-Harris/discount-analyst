### LLMJudge

Bases: `Evaluator[object, object, object]`

Judge whether the output of a language model meets the criteria of a provided rubric.

If you do not specify a model, it uses the default model for judging. This starts as 'openai:gpt-4o', but can be overridden by calling set_default_judge_model.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class LLMJudge(Evaluator[object, object, object]):
    """Judge whether the output of a language model meets the criteria of a provided rubric.

    If you do not specify a model, it uses the default model for judging. This starts as 'openai:gpt-4o', but can be
    overridden by calling [`set_default_judge_model`][pydantic_evals.evaluators.llm_as_a_judge.set_default_judge_model].
    """

    rubric: str
    model: models.Model | models.KnownModelName | None = None
    include_input: bool = False
    include_expected_output: bool = False
    model_settings: ModelSettings | None = None
    score: OutputConfig | Literal[False] = False
    assertion: OutputConfig | Literal[False] = field(default_factory=lambda: OutputConfig(include_reason=True))

    async def evaluate(
        self,
        ctx: EvaluatorContext[object, object, object],
    ) -> EvaluatorOutput:
        if self.include_input:
            if self.include_expected_output:
                from .llm_as_a_judge import judge_input_output_expected

                grading_output = await judge_input_output_expected(
                    ctx.inputs, ctx.output, ctx.expected_output, self.rubric, self.model, self.model_settings
                )
            else:
                from .llm_as_a_judge import judge_input_output

                grading_output = await judge_input_output(
                    ctx.inputs, ctx.output, self.rubric, self.model, self.model_settings
                )
        else:
            if self.include_expected_output:
                from .llm_as_a_judge import judge_output_expected

                grading_output = await judge_output_expected(
                    ctx.output, ctx.expected_output, self.rubric, self.model, self.model_settings
                )
            else:
                from .llm_as_a_judge import judge_output

                grading_output = await judge_output(ctx.output, self.rubric, self.model, self.model_settings)

        output: dict[str, EvaluationScalar | EvaluationReason] = {}
        include_both = self.score is not False and self.assertion is not False
        evaluation_name = self.get_default_evaluation_name()

        if self.score is not False:
            default_name = f'{evaluation_name}_score' if include_both else evaluation_name
            _update_combined_output(output, grading_output.score, grading_output.reason, self.score, default_name)

        if self.assertion is not False:
            default_name = f'{evaluation_name}_pass' if include_both else evaluation_name
            _update_combined_output(output, grading_output.pass_, grading_output.reason, self.assertion, default_name)

        return output

    def build_serialization_arguments(self):
        result = super().build_serialization_arguments()
        # always serialize the model as a string when present; use its name if it's a KnownModelName
        if (model := result.get('model')) and isinstance(model, models.Model):  # pragma: no branch
            result['model'] = f'{model.system}:{model.model_name}'

        # Note: this may lead to confusion if you try to serialize-then-deserialize with a custom model.
        # I expect that is rare enough to be worth not solving yet, but common enough that we probably will want to
        # solve it eventually. I'm imagining some kind of model registry, but don't want to work out the details yet.
        return result

```
