### Output validators

Some validation is inconvenient or impossible to do in Pydantic validators, in particular when the validation requires IO and is asynchronous. Pydantic AI provides a way to add validation functions via the agent.output_validator decorator.

If you want to implement separate validation logic for different output types, it's recommended to use [output functions](#output-functions) instead, to save you from having to do `isinstance` checks inside the output validator. If you want the model to output plain text, do your own processing or validation, and then have the agent's final output be the result of your function, it's recommended to use an [output function](#output-functions) with the [`TextOutput` marker class](#text-output).

Here's a simplified variant of the [SQL Generation example](../examples/sql-gen/):

sql_gen.py

```python
from fake_database import DatabaseConn, QueryError
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ModelRetry


class Success(BaseModel):
    sql_query: str


class InvalidRequest(BaseModel):
    error_message: str


Output = Success | InvalidRequest
agent = Agent[DatabaseConn, Output](
    'google-gla:gemini-2.5-flash',
    output_type=Output,  # type: ignore
    deps_type=DatabaseConn,
    system_prompt='Generate PostgreSQL flavored SQL queries based on user input.',
)


@agent.output_validator
async def validate_sql(ctx: RunContext[DatabaseConn], output: Output) -> Output:
    if isinstance(output, InvalidRequest):
        return output
    try:
        await ctx.deps.execute(f'EXPLAIN {output.sql_query}')
    except QueryError as e:
        raise ModelRetry(f'Invalid query: {e}') from e
    else:
        return output


result = agent.run_sync(
    'get me users who were last active yesterday.', deps=DatabaseConn()
)
print(result.output)
#> sql_query='SELECT * FROM users WHERE last_active::date = today() - interval 1 day'

```

_(This example is complete, it can be run "as is")_

#### Handling partial output in output validators

You can use the `partial_output` field on `RunContext` to handle validation differently for partial outputs during streaming (e.g. skip validation altogether).

[Learn about Gateway](../gateway) partial_validation_streaming.py

```python
from pydantic_ai import Agent, ModelRetry, RunContext

agent = Agent('gateway/openai:gpt-5')

@agent.output_validator
def validate_output(ctx: RunContext, output: str) -> str:
    if ctx.partial_output:
        return output
    else:
        if len(output) < 50:
            raise ModelRetry('Output is too short.')
        return output


async def main():
    async with agent.run_stream('Write a long story about a cat') as result:
        async for message in result.stream_text():
            print(message)
            #> Once upon a
            #> Once upon a time, there was
            #> Once upon a time, there was a curious cat
            #> Once upon a time, there was a curious cat named Whiskers who
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore the world around
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore the world around him...

```

partial_validation_streaming.py

```python
from pydantic_ai import Agent, ModelRetry, RunContext

agent = Agent('openai:gpt-5')

@agent.output_validator
def validate_output(ctx: RunContext, output: str) -> str:
    if ctx.partial_output:
        return output
    else:
        if len(output) < 50:
            raise ModelRetry('Output is too short.')
        return output


async def main():
    async with agent.run_stream('Write a long story about a cat') as result:
        async for message in result.stream_text():
            print(message)
            #> Once upon a
            #> Once upon a time, there was
            #> Once upon a time, there was a curious cat
            #> Once upon a time, there was a curious cat named Whiskers who
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore the world around
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore the world around him...

```

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_
