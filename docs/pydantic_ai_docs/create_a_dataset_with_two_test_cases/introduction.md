from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ExactMatch(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output == ctx.expected_output

dataset = Dataset(
    cases=[
        Case(name='test1', inputs={'text': 'Hello'}, expected_output='HELLO'),
        Case(name='test2', inputs={'text': 'World'}, expected_output='WORLD'),
    ],
    evaluators=[ExactMatch()],
)
