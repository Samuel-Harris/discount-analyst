### Using `GraphRun.next(node)` manually

Alternatively, you can drive iteration manually with the GraphRun.next method, which allows you to pass in whichever node you want to run next. You can modify or selectively skip nodes this way.

Below is a contrived example that stops whenever the counter is at 2, ignoring any node runs beyond that:

count_down_next.py

```python
from pydantic_graph import End, FullStatePersistence
from count_down import CountDown, CountDownState, count_down_graph


async def main():
    state = CountDownState(counter=5)
    persistence = FullStatePersistence()  # (7)!
    async with count_down_graph.iter(
        CountDown(), state=state, persistence=persistence
    ) as run:
        node = run.next_node  # (1)!
        while not isinstance(node, End):  # (2)!
            print('Node:', node)
            #> Node: CountDown()
            #> Node: CountDown()
            #> Node: CountDown()
            #> Node: CountDown()
            if state.counter == 2:
                break  # (3)!
            node = await run.next(node)  # (4)!

        print(run.result)  # (5)!
        #> None

        for step in persistence.history:  # (6)!
            print('History Step:', step.state, step.state)
            #> History Step: CountDownState(counter=5) CountDownState(counter=5)
            #> History Step: CountDownState(counter=4) CountDownState(counter=4)
            #> History Step: CountDownState(counter=3) CountDownState(counter=3)
            #> History Step: CountDownState(counter=2) CountDownState(counter=2)

```

1. We start by grabbing the first node that will be run in the agent's graph.
1. The agent run is finished once an `End` node has been produced; instances of `End` cannot be passed to `next`.
1. If the user decides to stop early, we break out of the loop. The graph run won't have a real final result in that case (`run.result` remains `None`).
1. At each step, we call `await run.next(node)` to run it and get the next node (or an `End`).
1. Because we did not continue the run until it finished, the `result` is not set.
1. The run's history is still populated with the steps we executed so far.
1. Use FullStatePersistence so we can show the history of the run, see [State Persistence](#state-persistence) below for more information.
