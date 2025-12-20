## Usage

You can then use HuggingFaceModel by name:

```python
from pydantic_ai import Agent

agent = Agent('huggingface:Qwen/Qwen3-235B-A22B')
...

```

Or initialise the model directly with just the model name:

```python
from pydantic_ai import Agent
from pydantic_ai.models.huggingface import HuggingFaceModel

model = HuggingFaceModel('Qwen/Qwen3-235B-A22B')
agent = Agent(model)
...

```

By default, the HuggingFaceModel uses the HuggingFaceProvider that will select automatically the first of the inference providers (Cerebras, Together AI, Cohere..etc) available for the model, sorted by your preferred order in https://hf.co/settings/inference-providers.
