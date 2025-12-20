### Agent

Now it's time to get into Pydantic AI and define the agent that will do the actual analysis!

We specify the model we'll use (`openai:gpt-5`), provide [instructions](../../agents/#instructions), give the agent access to the [DuckDuckGo search tool](../../common-tools/#duckduckgo-search-tool), and tell it to output either an `Analysis` or `None` using the [Native Output](../../output/#native-output) structured output mode.

The real meat of the app is in the instructions that tell the agent how to evaluate each new Slack member. If you plan to use this app yourself, you'll of course want to modify them to your own situation.

[Learn about Gateway](../../gateway) [slack_lead_qualifier/agent.py (L7-L40)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/agent.py#L7-L40)

```python
...

from pydantic_ai import Agent, NativeOutput
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

...

agent = Agent(
    'gateway/openai:gpt-5',
    instructions=dedent(
        """
        When a new person joins our public Slack, please put together a brief snapshot so we can be most useful to them.

        **What to include**

        1. **Who they are:**  Any details about their professional role or projects (e.g. LinkedIn, GitHub, company bio).
        2. **Where they work:**  Name of the organisation and its domain.
        3. **How we can help:**  On a scale of 1â€“5, estimate how likely they are to benefit from **Pydantic Logfire**
           (our paid observability tool) based on factors such as company size, product maturity, or AI usage.
           *1 = probably not relevant, 5 = very strong fit.*

        **Our products (for context only)**
        â€¢ **Pydantic Validation** â€“ Python data-validation (open source)
        â€¢ **Pydantic AI** â€“ Python agent framework (open source)
        â€¢ **Pydantic Logfire** â€“ Observability for traces, logs & metrics with first-class AI support (commercial)

        **How to research**

        â€¢ Use the provided DuckDuckGo search tool to research the person and the organization they work for, based on the email domain or what you find on e.g. LinkedIn and GitHub.
        â€¢ If you can't find enough to form a reasonable view, return **None**.
        """
    ),
    tools=[duckduckgo_search_tool()],
    output_type=NativeOutput([Analysis, NoneType]),
)

...

```

[slack_lead_qualifier/agent.py (L7-L40)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/agent.py#L7-L40)

```python
...

from pydantic_ai import Agent, NativeOutput
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

...

agent = Agent(
    'openai:gpt-5',
    instructions=dedent(
        """
        When a new person joins our public Slack, please put together a brief snapshot so we can be most useful to them.

        **What to include**

        1. **Who they are:**  Any details about their professional role or projects (e.g. LinkedIn, GitHub, company bio).
        2. **Where they work:**  Name of the organisation and its domain.
        3. **How we can help:**  On a scale of 1â€“5, estimate how likely they are to benefit from **Pydantic Logfire**
           (our paid observability tool) based on factors such as company size, product maturity, or AI usage.
           *1 = probably not relevant, 5 = very strong fit.*

        **Our products (for context only)**
        â€¢ **Pydantic Validation** â€“ Python data-validation (open source)
        â€¢ **Pydantic AI** â€“ Python agent framework (open source)
        â€¢ **Pydantic Logfire** â€“ Observability for traces, logs & metrics with first-class AI support (commercial)

        **How to research**

        â€¢ Use the provided DuckDuckGo search tool to research the person and the organization they work for, based on the email domain or what you find on e.g. LinkedIn and GitHub.
        â€¢ If you can't find enough to form a reasonable view, return **None**.
        """
    ),
    tools=[duckduckgo_search_tool()],
    output_type=NativeOutput([Analysis, NoneType]),
)

...

```

#### `analyze_profile`

We also define a `analyze_profile` helper function that takes a `Profile`, runs the agent, and returns an `Analysis` (or `None`), and instrument it using [Logfire](../../logfire/).

[slack_lead_qualifier/agent.py (L44-L47)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/agent.py#L44-L47)

```python
...

@logfire.instrument('Analyze profile')
async def analyze_profile(profile: Profile) -> Analysis | None:
    result = await agent.run(profile.as_prompt())
    return result.output

```
