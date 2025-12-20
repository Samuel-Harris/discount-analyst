### GraphRunContext

GraphRunContext â€” The context for the graph run, similar to Pydantic AI's RunContext. This holds the state of the graph and dependencies and is passed to nodes when they're run.

`GraphRunContext` is generic in the state type of the graph it's used in, StateT.
