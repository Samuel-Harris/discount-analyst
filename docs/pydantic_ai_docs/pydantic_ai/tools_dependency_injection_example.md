## Tools & Dependency Injection Example

Here is a concise example using Pydantic AI to build a support agent for a bank:

[Learn about Gateway](../gateway) bank_support.py

```python
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from bank_database import DatabaseConn


@dataclass
class SupportDependencies:  # (3)!
    customer_id: int
    db: DatabaseConn  # (12)!


class SupportOutput(BaseModel):  # (13)!
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description="Whether to block the customer's card")
    risk: int = Field(description='Risk level of query', ge=0, le=10)


support_agent = Agent(  # (1)!
    'gateway/openai:gpt-5',  # (2)!
    deps_type=SupportDependencies,
    output_type=SupportOutput,  # (9)!
    instructions=(  # (4)!
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
    ),
)


@support_agent.instructions  # (5)!
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name!r}"


@support_agent.tool  # (6)!
async def customer_balance(
    ctx: RunContext[SupportDependencies], include_pending: bool
) -> float:
    """Returns the customer's current account balance."""  # (7)!
    return await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )


...  # (11)!


async def main():
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())
    result = await support_agent.run('What is my balance?', deps=deps)  # (8)!
    print(result.output)  # (10)!
    """
    support_advice='Hello John, your current account balance, including pending transactions, is $123.45.' block_card=False risk=1
    """

    result = await support_agent.run('I just lost my card!', deps=deps)
    print(result.output)
    """
    support_advice="I'm sorry to hear that, John. We are temporarily blocking your card to prevent unauthorized transactions." block_card=True risk=8
    """

```

1. This [agent](agents/) will act as first-tier support in a bank. Agents are generic in the type of dependencies they accept and the type of output they return. In this case, the support agent has type `Agent[SupportDependencies, SupportOutput]`.
1. Here we configure the agent to use [OpenAI's GPT-5 model](api/models/openai/), you can also set the model when running the agent.
1. The `SupportDependencies` dataclass is used to pass data, connections, and logic into the model that will be needed when running [instructions](agents/#instructions) and [tool](tools/) functions. Pydantic AI's system of dependency injection provides a [type-safe](agents/#static-type-checking) way to customise the behavior of your agents, and can be especially useful when running [unit tests](testing/) and evals.
1. Static [instructions](agents/#instructions) can be registered with the instructions keyword argument to the agent.
1. Dynamic [instructions](agents/#instructions) can be registered with the @agent.instructions decorator, and can make use of dependency injection. Dependencies are carried via the RunContext argument, which is parameterized with the `deps_type` from above. If the type annotation here is wrong, static type checkers will catch it.
1. The [`@agent.tool`](tools/) decorator let you register functions which the LLM may call while responding to a user. Again, dependencies are carried via RunContext, any other arguments become the tool schema passed to the LLM. Pydantic is used to validate these arguments, and errors are passed back to the LLM so it can retry.
1. The docstring of a tool is also passed to the LLM as the description of the tool. Parameter descriptions are [extracted](tools/#function-tools-and-schema) from the docstring and added to the parameter schema sent to the LLM.
1. [Run the agent](agents/#running-agents) asynchronously, conducting a conversation with the LLM until a final response is reached. Even in this fairly simple case, the agent will exchange multiple messages with the LLM as tools are called to retrieve an output.
1. The response from the agent will be guaranteed to be a `SupportOutput`. If validation fails [reflection](agents/#reflection-and-self-correction), the agent is prompted to try again.
1. The output will be validated with Pydantic to guarantee it is a `SupportOutput`, since the agent is generic, it'll also be typed as a `SupportOutput` to aid with static type checking.
1. In a real use case, you'd add more tools and longer instructions to the agent to extend the context it's equipped with and support it can provide.
1. This is a simple sketch of a database connection, used to keep the example short and readable. In reality, you'd be connecting to an external database (e.g. PostgreSQL) to get information about customers.
1. This [Pydantic](https://docs.pydantic.dev) model is used to constrain the structured data returned by the agent. From this simple definition, Pydantic builds the JSON Schema that tells the LLM how to return the data, and performs validation to guarantee the data is correct at the end of the run.

bank_support.py

```python
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from bank_database import DatabaseConn


@dataclass
class SupportDependencies:  # (3)!
    customer_id: int
    db: DatabaseConn  # (12)!


class SupportOutput(BaseModel):  # (13)!
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description="Whether to block the customer's card")
    risk: int = Field(description='Risk level of query', ge=0, le=10)


support_agent = Agent(  # (1)!
    'openai:gpt-5',  # (2)!
    deps_type=SupportDependencies,
    output_type=SupportOutput,  # (9)!
    instructions=(  # (4)!
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
    ),
)


@support_agent.instructions  # (5)!
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name!r}"


@support_agent.tool  # (6)!
async def customer_balance(
    ctx: RunContext[SupportDependencies], include_pending: bool
) -> float:
    """Returns the customer's current account balance."""  # (7)!
    return await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )


...  # (11)!


async def main():
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())
    result = await support_agent.run('What is my balance?', deps=deps)  # (8)!
    print(result.output)  # (10)!
    """
    support_advice='Hello John, your current account balance, including pending transactions, is $123.45.' block_card=False risk=1
    """

    result = await support_agent.run('I just lost my card!', deps=deps)
    print(result.output)
    """
    support_advice="I'm sorry to hear that, John. We are temporarily blocking your card to prevent unauthorized transactions." block_card=True risk=8
    """

```

1. This [agent](agents/) will act as first-tier support in a bank. Agents are generic in the type of dependencies they accept and the type of output they return. In this case, the support agent has type `Agent[SupportDependencies, SupportOutput]`.
1. Here we configure the agent to use [OpenAI's GPT-5 model](api/models/openai/), you can also set the model when running the agent.
1. The `SupportDependencies` dataclass is used to pass data, connections, and logic into the model that will be needed when running [instructions](agents/#instructions) and [tool](tools/) functions. Pydantic AI's system of dependency injection provides a [type-safe](agents/#static-type-checking) way to customise the behavior of your agents, and can be especially useful when running [unit tests](testing/) and evals.
1. Static [instructions](agents/#instructions) can be registered with the instructions keyword argument to the agent.
1. Dynamic [instructions](agents/#instructions) can be registered with the @agent.instructions decorator, and can make use of dependency injection. Dependencies are carried via the RunContext argument, which is parameterized with the `deps_type` from above. If the type annotation here is wrong, static type checkers will catch it.
1. The [`@agent.tool`](tools/) decorator let you register functions which the LLM may call while responding to a user. Again, dependencies are carried via RunContext, any other arguments become the tool schema passed to the LLM. Pydantic is used to validate these arguments, and errors are passed back to the LLM so it can retry.
1. The docstring of a tool is also passed to the LLM as the description of the tool. Parameter descriptions are [extracted](tools/#function-tools-and-schema) from the docstring and added to the parameter schema sent to the LLM.
1. [Run the agent](agents/#running-agents) asynchronously, conducting a conversation with the LLM until a final response is reached. Even in this fairly simple case, the agent will exchange multiple messages with the LLM as tools are called to retrieve an output.
1. The response from the agent will be guaranteed to be a `SupportOutput`. If validation fails [reflection](agents/#reflection-and-self-correction), the agent is prompted to try again.
1. The output will be validated with Pydantic to guarantee it is a `SupportOutput`, since the agent is generic, it'll also be typed as a `SupportOutput` to aid with static type checking.
1. In a real use case, you'd add more tools and longer instructions to the agent to extend the context it's equipped with and support it can provide.
1. This is a simple sketch of a database connection, used to keep the example short and readable. In reality, you'd be connecting to an external database (e.g. PostgreSQL) to get information about customers.
1. This [Pydantic](https://docs.pydantic.dev) model is used to constrain the structured data returned by the agent. From this simple definition, Pydantic builds the JSON Schema that tells the LLM how to return the data, and performs validation to guarantee the data is correct at the end of the run.

Complete `bank_support.py` example

The code included here is incomplete for the sake of brevity (the definition of `DatabaseConn` is missing); you can find the complete `bank_support.py` example [here](examples/bank-support/).
