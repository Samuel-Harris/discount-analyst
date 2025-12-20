### Tool Based Generative UI

Demonstrates customised rendering for tool output with used confirmation.

If you've [run the example](#running-the-example), you can view it at <http://localhost:3000/pydantic-ai/feature/tool_based_generative_ui>.

#### Haiku Tools

- `generate_haiku` - AG-UI tool to display a haiku in English and Japanese

#### Haiku Prompt

```text
Generate a haiku about formula 1

```

#### Tool Based Generative UI - Code

[Learn about Gateway](../../gateway) [ag_ui/api/tool_based_generative_ui.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/ag_ui/api/tool_based_generative_ui.py)

```python
"""Tool Based Generative UI feature.

No special handling is required for this feature.
"""

from __future__ import annotations

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui.app import AGUIApp

agent = Agent('gateway/openai:gpt-5-mini')
app = AGUIApp(agent)

```

[ag_ui/api/tool_based_generative_ui.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/ag_ui/api/tool_based_generative_ui.py)

```python
"""Tool Based Generative UI feature.

No special handling is required for this feature.
"""

from __future__ import annotations

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui.app import AGUIApp

agent = Agent('openai:gpt-5-mini')
app = AGUIApp(agent)

```

Small but complete example of using Pydantic AI to build a support agent for a bank.

Demonstrates:

- [dynamic system prompt](../../agents/#system-prompts)
- [structured `output_type`](../../output/#structured-output)
- [tools](../../tools/)
