## Configure the provider

If you want to pass parameters in code to the provider, you can programmatically instantiate the HuggingFaceProvider and pass it to the model:

```python
from pydantic_ai import Agent
from pydantic_ai.models.huggingface import HuggingFaceModel
from pydantic_ai.providers.huggingface import HuggingFaceProvider

model = HuggingFaceModel('Qwen/Qwen3-235B-A22B', provider=HuggingFaceProvider(api_key='hf_token', provider_name='nebius'))
agent = Agent(model)
...

```
