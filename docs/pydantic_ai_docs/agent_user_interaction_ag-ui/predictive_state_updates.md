### Predictive State Updates

Demonstrates how to use the predictive state updates feature to update the state of the UI based on agent responses, including user interaction via user confirmation.

If you've [run the example](#running-the-example), you can view it at <http://localhost:3000/pydantic-ai/feature/predictive_state_updates>.

#### Story Tools

- `write_document` - AG-UI tool to write the document to a window
- `document_predict_state` - Pydantic AI tool that enables document state prediction for the `write_document` tool

This also shows how to use custom instructions based on shared state information.

#### Story Example

Starting document text

```markdown
Bruce was a good dog,
```

Agent prompt

```text
Help me complete my story about bruce the dog, is should be no longer than a sentence.

```

#### Predictive State Updates - Code

[Learn about Gateway](../../gateway) [ag_ui/api/predictive_state_updates.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/ag_ui/api/predictive_state_updates.py)

```python
"""Predictive State feature."""

from __future__ import annotations

from textwrap import dedent

from pydantic import BaseModel

from ag_ui.core import CustomEvent, EventType
from pydantic_ai import Agent, RunContext
from pydantic_ai.ui import StateDeps
from pydantic_ai.ui.ag_ui.app import AGUIApp


class DocumentState(BaseModel):
    """State for the document being written."""

    document: str = ''


agent = Agent('gateway/openai:gpt-5-mini', deps_type=StateDeps[DocumentState])
