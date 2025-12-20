Writing unit tests for Pydantic AI code is just like unit tests for any other Python code.

Because for the most part they're nothing new, we have pretty well established tools and patterns for writing and running these kinds of tests.

Unless you're really sure you know better, you'll probably want to follow roughly this strategy:

- Use [`pytest`](https://docs.pytest.org/en/stable/) as your test harness
- If you find yourself typing out long assertions, use [inline-snapshot](https://15r10nk.github.io/inline-snapshot/latest/)
- Similarly, [dirty-equals](https://dirty-equals.helpmanual.io/latest/) can be useful for comparing large data structures
- Use TestModel or FunctionModel in place of your actual model to avoid the usage, latency and variability of real LLM calls
- Use Agent.override to replace an agent's model, dependencies, or toolsets inside your application logic
- Set ALLOW_MODEL_REQUESTS=False globally to block any requests from being made to non-test models accidentally
