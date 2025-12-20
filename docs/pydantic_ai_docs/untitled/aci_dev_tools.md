### ACI.dev Tools

If you'd like to use tools from the [ACI.dev tool library](https://www.aci.dev/tools) with Pydantic AI, you can use the ACIToolset [toolset](./) which takes a list of ACI tool names as well as the `linked_account_owner_id`. Note that Pydantic AI will not validate the arguments in this case -- it's up to the model to provide arguments matching the schema specified by the ACI tool, and up to the ACI tool to raise an error if the arguments are invalid.

You will need to install the `aci-sdk` package, set your ACI API key in the `ACI_API_KEY` environment variable, and pass your ACI "linked account owner ID" to the function.

[Learn about Gateway](../gateway)

```python
import os

from pydantic_ai import Agent
from pydantic_ai.ext.aci import ACIToolset

toolset = ACIToolset(
    [
        'OPEN_WEATHER_MAP__CURRENT_WEATHER',
        'OPEN_WEATHER_MAP__FORECAST',
    ],
    linked_account_owner_id=os.getenv('LINKED_ACCOUNT_OWNER_ID'),
)

agent = Agent('gateway/openai:gpt-5', toolsets=[toolset])

```

```python
import os

from pydantic_ai import Agent
from pydantic_ai.ext.aci import ACIToolset

toolset = ACIToolset(
    [
        'OPEN_WEATHER_MAP__CURRENT_WEATHER',
        'OPEN_WEATHER_MAP__FORECAST',
    ],
    linked_account_owner_id=os.getenv('LINKED_ACCOUNT_OWNER_ID'),
)

agent = Agent('openai:gpt-5', toolsets=[toolset])

```
