## Custom Hugging Face client

HuggingFaceProvider also accepts a custom [`AsyncInferenceClient`](https://huggingface.co/docs/huggingface_hub/v0.29.3/en/package_reference/inference_client#huggingface_hub.AsyncInferenceClient) client via the `hf_client` parameter, so you can customise the `headers`, `bill_to` (billing to an HF organization you're a member of), `base_url` etc. as defined in the [Hugging Face Hub python library docs](https://huggingface.co/docs/huggingface_hub/package_reference/inference_client).

```python
from huggingface_hub import AsyncInferenceClient

from pydantic_ai import Agent
from pydantic_ai.models.huggingface import HuggingFaceModel
from pydantic_ai.providers.huggingface import HuggingFaceProvider

client = AsyncInferenceClient(
    bill_to='openai',
    api_key='hf_token',
    provider='fireworks-ai',
)

model = HuggingFaceModel(
    'Qwen/Qwen3-235B-A22B',
    provider=HuggingFaceProvider(hf_client=client),
)
agent = Agent(model)
...

```
