## Evaluators

Evaluators analyze and score the results of your Task when tested against a Case.

These can be deterministic, code-based checks (such as testing model output format with a regex, or checking for the appearance of PII or sensitive data), or they can assess non-deterministic model outputs for qualities like accuracy, precision/recall, hallucinations, or instruction-following.

While both kinds of testing are useful in LLM systems, classical code-based tests are cheaper and easier than tests which require either human or machine review of model outputs.

Pydantic Evals includes several [built-in evaluators](evaluators/built-in/) and allows you to define [custom evaluators](evaluators/custom/):

simple_eval_evaluator.py

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.evaluators.common import IsInstance

from simple_eval_dataset import dataset

dataset.add_evaluator(IsInstance(type_name='str'))  # (1)!


@dataclass
class MyEvaluator(Evaluator):
    async def evaluate(self, ctx: EvaluatorContext[str, str]) -> float:  # (2)!
        if ctx.output == ctx.expected_output:
            return 1.0
        elif (
            isinstance(ctx.output, str)
            and ctx.expected_output.lower() in ctx.output.lower()
        ):
            return 0.8
        else:
            return 0.0


dataset.add_evaluator(MyEvaluator())

```

1. You can add built-in evaluators to a dataset using the add_evaluator method.
1. This custom evaluator returns a simple score based on whether the output matches the expected output.

_(This example is complete, it can be run "as is")_

Learn more:

- [Evaluators Overview](evaluators/overview/) - When to use different types
- [Built-in Evaluators](evaluators/built-in/) - Complete reference
- [LLM Judge](evaluators/llm-judge/) - Using LLMs as evaluators
- [Custom Evaluators](evaluators/custom/) - Write your own logic
- [Span-Based Evaluation](evaluators/span-based/) - Analyze execution traces
