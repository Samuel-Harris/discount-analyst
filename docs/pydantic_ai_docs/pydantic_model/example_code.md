## Example Code

[pydantic_model.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/pydantic_model.py)

```python
"""Simple example of using Pydantic AI to construct a Pydantic model from a text input.

Run with:

    uv run -m pydantic_ai_examples.pydantic_model
"""

import os

import logfire
from pydantic import BaseModel

from pydantic_ai import Agent
