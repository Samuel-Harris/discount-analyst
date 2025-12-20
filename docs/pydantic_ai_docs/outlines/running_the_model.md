## Running the model

Once you have initialized an `OutlinesModel`, you can use it with an Agent as with all other Pydantic AI models.

As Outlines is focused on structured output, this provider supports the `output_type` component through the NativeOutput format. There is not need to include information on the required output format in your prompt, instructions based on the `output_type` will be included automatically.

```python
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from pydantic_ai import Agent
from pydantic_ai.models.outlines import OutlinesModel
from pydantic_ai.settings import ModelSettings


class Box(BaseModel):
    """Class representing a box"""
    width: int
    height: int
    depth: int
    units: str

model = OutlinesModel.from_transformers(
    AutoModelForCausalLM.from_pretrained('microsoft/Phi-3-mini-4k-instruct'),
    AutoTokenizer.from_pretrained('microsoft/Phi-3-mini-4k-instruct')
)
agent = Agent(model, output_type=Box)

result = agent.run_sync(
    'Give me the dimensions of a box',
    model_settings=ModelSettings(extra_body={'max_new_tokens': 100})
)
print(result.output) # width=20 height=30 depth=40 units='cm'

```

Outlines does not support tools yet, but support for that feature will be added in the near future.
