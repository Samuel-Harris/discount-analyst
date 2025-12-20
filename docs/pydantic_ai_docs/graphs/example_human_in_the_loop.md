### Example: Human in the loop.

As noted above, state persistence allows graphs to be interrupted and resumed. One use case of this is to allow user input to continue.

In this example, an AI asks the user a question, the user provides an answer, the AI evaluates the answer and ends if the user got it right or asks another question if they got it wrong.

Instead of running the entire graph in a single process invocation, we run the graph by running the process repeatedly, optionally providing an answer to the question as a command line argument.

`ai_q_and_a_graph.py` â€” `question_graph` definition

[Learn about Gateway](../gateway) ai_q_and_a_graph.py

```python
from __future__ import annotations as _annotations

from typing import Annotated
from pydantic_graph import Edge
from dataclasses import dataclass, field
from pydantic import BaseModel
from pydantic_graph import (
    BaseNode,
    End,
    Graph,
    GraphRunContext,
)
from pydantic_ai import Agent, format_as_xml
from pydantic_ai import ModelMessage

ask_agent = Agent('gateway/openai:gpt-5', output_type=str, instrument=True)


@dataclass
class QuestionState:
    question: str | None = None
    ask_agent_messages: list[ModelMessage] = field(default_factory=list)
    evaluate_agent_messages: list[ModelMessage] = field(default_factory=list)


@dataclass
class Ask(BaseNode[QuestionState]):
    """Generate question using GPT-5."""
    docstring_notes = True
    async def run(
        self, ctx: GraphRunContext[QuestionState]
    ) -> Annotated[Answer, Edge(label='Ask the question')]:
        result = await ask_agent.run(
            'Ask a simple question with a single correct answer.',
            message_history=ctx.state.ask_agent_messages,
        )
        ctx.state.ask_agent_messages += result.new_messages()
        ctx.state.question = result.output
        return Answer(result.output)


@dataclass
class Answer(BaseNode[QuestionState]):
    question: str

    async def run(self, ctx: GraphRunContext[QuestionState]) -> Evaluate:
        answer = input(f'{self.question}: ')
        return Evaluate(answer)


class EvaluationResult(BaseModel, use_attribute_docstrings=True):
    correct: bool
    """Whether the answer is correct."""
    comment: str
    """Comment on the answer, reprimand the user if the answer is wrong."""


evaluate_agent = Agent(
    'gateway/openai:gpt-5',
    output_type=EvaluationResult,
    system_prompt='Given a question and answer, evaluate if the answer is correct.',
)


@dataclass
class Evaluate(BaseNode[QuestionState, None, str]):
    answer: str

    async def run(
        self,
        ctx: GraphRunContext[QuestionState],
    ) -> Annotated[End[str], Edge(label='success')] | Reprimand:
        assert ctx.state.question is not None
        result = await evaluate_agent.run(
            format_as_xml({'question': ctx.state.question, 'answer': self.answer}),
            message_history=ctx.state.evaluate_agent_messages,
        )
        ctx.state.evaluate_agent_messages += result.new_messages()
        if result.output.correct:
            return End(result.output.comment)
        else:
            return Reprimand(result.output.comment)


@dataclass
class Reprimand(BaseNode[QuestionState]):
    comment: str

    async def run(self, ctx: GraphRunContext[QuestionState]) -> Ask:
        print(f'Comment: {self.comment}')
        ctx.state.question = None
        return Ask()


question_graph = Graph(
    nodes=(Ask, Answer, Evaluate, Reprimand), state_type=QuestionState
)

```

ai_q_and_a_graph.py

```python
from __future__ import annotations as _annotations

from typing import Annotated
from pydantic_graph import Edge
from dataclasses import dataclass, field
from pydantic import BaseModel
from pydantic_graph import (
    BaseNode,
    End,
    Graph,
    GraphRunContext,
)
from pydantic_ai import Agent, format_as_xml
from pydantic_ai import ModelMessage

ask_agent = Agent('openai:gpt-5', output_type=str, instrument=True)


@dataclass
class QuestionState:
    question: str | None = None
    ask_agent_messages: list[ModelMessage] = field(default_factory=list)
    evaluate_agent_messages: list[ModelMessage] = field(default_factory=list)


@dataclass
class Ask(BaseNode[QuestionState]):
    """Generate question using GPT-5."""
    docstring_notes = True
    async def run(
        self, ctx: GraphRunContext[QuestionState]
    ) -> Annotated[Answer, Edge(label='Ask the question')]:
        result = await ask_agent.run(
            'Ask a simple question with a single correct answer.',
            message_history=ctx.state.ask_agent_messages,
        )
        ctx.state.ask_agent_messages += result.new_messages()
        ctx.state.question = result.output
        return Answer(result.output)


@dataclass
class Answer(BaseNode[QuestionState]):
    question: str

    async def run(self, ctx: GraphRunContext[QuestionState]) -> Evaluate:
        answer = input(f'{self.question}: ')
        return Evaluate(answer)


class EvaluationResult(BaseModel, use_attribute_docstrings=True):
    correct: bool
    """Whether the answer is correct."""
    comment: str
    """Comment on the answer, reprimand the user if the answer is wrong."""


evaluate_agent = Agent(
    'openai:gpt-5',
    output_type=EvaluationResult,
    system_prompt='Given a question and answer, evaluate if the answer is correct.',
)


@dataclass
class Evaluate(BaseNode[QuestionState, None, str]):
    answer: str

    async def run(
        self,
        ctx: GraphRunContext[QuestionState],
    ) -> Annotated[End[str], Edge(label='success')] | Reprimand:
        assert ctx.state.question is not None
        result = await evaluate_agent.run(
            format_as_xml({'question': ctx.state.question, 'answer': self.answer}),
            message_history=ctx.state.evaluate_agent_messages,
        )
        ctx.state.evaluate_agent_messages += result.new_messages()
        if result.output.correct:
            return End(result.output.comment)
        else:
            return Reprimand(result.output.comment)


@dataclass
class Reprimand(BaseNode[QuestionState]):
    comment: str

    async def run(self, ctx: GraphRunContext[QuestionState]) -> Ask:
        print(f'Comment: {self.comment}')
        ctx.state.question = None
        return Ask()


question_graph = Graph(
    nodes=(Ask, Answer, Evaluate, Reprimand), state_type=QuestionState
)

```

_(This example is complete, it can be run "as is")_

ai_q_and_a_run.py

```python
import sys
from pathlib import Path

from pydantic_graph import End
from pydantic_graph.persistence.file import FileStatePersistence
from pydantic_ai import ModelMessage  # noqa: F401

from ai_q_and_a_graph import Ask, question_graph, Evaluate, QuestionState, Answer


async def main():
    answer: str | None = sys.argv[1] if len(sys.argv) > 1 else None  # (1)!
    persistence = FileStatePersistence(Path('question_graph.json'))  # (2)!
    persistence.set_graph_types(question_graph)  # (3)!

    if snapshot := await persistence.load_next():  # (4)!
        state = snapshot.state
        assert answer is not None
        node = Evaluate(answer)
    else:
        state = QuestionState()
        node = Ask()  # (5)!

    async with question_graph.iter(node, state=state, persistence=persistence) as run:
        while True:
            node = await run.next()  # (6)!
            if isinstance(node, End):  # (7)!
                print('END:', node.data)
                history = await persistence.load_all()  # (8)!
                print([e.node for e in history])
                break
            elif isinstance(node, Answer):  # (9)!
                print(node.question)
                #> What is the capital of France?
                break
            # otherwise just continue

```

1. Get the user's answer from the command line, if provided. See [question graph example](../examples/question-graph/) for a complete example.
1. Create a state persistence instance the `'question_graph.json'` file may or may not already exist.
1. Since we're using the persistence interface outside a graph, we need to call set_graph_types to set the graph generic types `StateT` and `RunEndT` for the persistence instance. This is necessary to allow the persistence instance to know how to serialize and deserialize graph nodes.
1. If we're run the graph before, load_next will return a snapshot of the next node to run, here we use `state` from that snapshot, and create a new `Evaluate` node with the answer provided on the command line.
1. If the graph hasn't been run before, we create a new `QuestionState` and start with the `Ask` node.
1. Call GraphRun.next() to run the node. This will return either a node or an `End` object.
1. If the node is an `End` object, the graph run is complete. The `data` field of the `End` object contains the comment returned by the `evaluate_agent` about the correct answer.
1. To demonstrate the state persistence, we call load_all to get all the snapshots from the persistence instance. This will return a list of Snapshot objects.
1. If the node is an `Answer` object, we print the question and break out of the loop to end the process and wait for user input.

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

For a complete example of this graph, see the [question graph example](../examples/question-graph/).
