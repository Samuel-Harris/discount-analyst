### Streaming Structured Output

Here's an example of streaming a user profile as it's built:

[Learn about Gateway](../gateway) streamed_user_profile.py

```python
from datetime import date

from typing_extensions import NotRequired, TypedDict

from pydantic_ai import Agent


class UserProfile(TypedDict):
    name: str
    dob: NotRequired[date]
    bio: NotRequired[str]


agent = Agent(
    'gateway/openai:gpt-5',
    output_type=UserProfile,
    system_prompt='Extract a user profile from the input',
)


async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    async with agent.run_stream(user_input) as result:
        async for profile in result.stream_output():
            print(profile)
            #> {'name': 'Ben'}
            #> {'name': 'Ben'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the '}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyr'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}

```

streamed_user_profile.py

```python
from datetime import date

from typing_extensions import NotRequired, TypedDict

from pydantic_ai import Agent


class UserProfile(TypedDict):
    name: str
    dob: NotRequired[date]
    bio: NotRequired[str]


agent = Agent(
    'openai:gpt-5',
    output_type=UserProfile,
    system_prompt='Extract a user profile from the input',
)


async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    async with agent.run_stream(user_input) as result:
        async for profile in result.stream_output():
            print(profile)
            #> {'name': 'Ben'}
            #> {'name': 'Ben'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the '}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyr'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}

```

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_

As setting an `output_type` uses the [Tool Output](#tool-output) mode by default, this will only work if the model supports streaming tool arguments. For models that don't, like Gemini, try [Native Output](#native-output) or [Prompted Output](#prompted-output) instead.
