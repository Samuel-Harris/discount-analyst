There are roughly four levels of complexity when building applications with Pydantic AI:

1. Single agent workflows â€” what most of the `pydantic_ai` documentation covers
1. [Agent delegation](#agent-delegation) â€” agents using another agent via tools
1. [Programmatic agent hand-off](#programmatic-agent-hand-off) â€” one agent runs, then application code calls another agent
1. [Graph based control flow](../graph/) â€” for the most complex cases, a graph-based state machine can be used to control the execution of multiple agents

Of course, you can combine multiple strategies in a single application.
