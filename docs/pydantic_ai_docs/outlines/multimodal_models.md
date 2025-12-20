## Multimodal models

If the model you are running through Outlines and the provider selected supports it, you can include images in your prompts using ImageUrl or BinaryImage. In that case, the prompt you provide when running the agent should be a list containing a string and one or several images. See the [input documentation](../../input/) for details and examples on using assets in model inputs.

This feature is supported in Outlines for the `SGLang` and `Transformers` models. If you want to run a multimodal model through `transformers`, you must provide a processor instead of a tokenizer as the second argument when initializing the model with the `OutlinesModel.from_transformers` method.

```python
from datetime import date
from typing import Literal

import torch
from pydantic import BaseModel
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

from pydantic_ai import Agent, ModelSettings
from pydantic_ai.messages import ImageUrl
from pydantic_ai.models.outlines import OutlinesModel

MODEL_NAME = 'Qwen/Qwen2-VL-7B-Instruct'

class Item(BaseModel):
    name: str
    quantity: int | None
    price_per_unit: float | None
    total_price: float | None

class ReceiptSummary(BaseModel):
    store_name: str
    store_address: str
    store_number: int | None
    items: list[Item]
    tax: float | None
    total: float | None
    date: date
    payment_method: Literal['cash', 'credit', 'debit', 'check', 'other']

tf_model = Qwen2VLForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    device_map='auto',
    dtype=torch.bfloat16
)
tf_processor = AutoProcessor.from_pretrained(
    MODEL_NAME,
    device_map='auto'
)
model = OutlinesModel.from_transformers(tf_model, tf_processor)

agent = Agent(model, output_type=ReceiptSummary)

result = agent.run_sync(
    [
        'You are an expert at extracting information from receipts. Please extract the information from the receipt. Be as detailed as possible, do not miss any information',
        ImageUrl('https://raw.githubusercontent.com/dottxt-ai/outlines/refs/heads/main/docs/examples/images/trader-joes-receipt.jpg')
    ],
    model_settings=ModelSettings(extra_body={'max_new_tokens': 1000})
)
print(result.output)
