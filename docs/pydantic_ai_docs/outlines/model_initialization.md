## Model Initialization

As Outlines is not an inference provider, but instead a library allowing you to run both local and API-based models, instantiating the model is a bit different from the other models available on Pydantic AI.

To initialize the `OutlinesModel` through the `__init__` method, the first argument you must provide has to be an `outlines.Model` or an `outlines.AsyncModel` instance.

For instance:

```python
import outlines
from transformers import AutoModelForCausalLM, AutoTokenizer

from pydantic_ai.models.outlines import OutlinesModel

outlines_model = outlines.from_transformers(
    AutoModelForCausalLM.from_pretrained('erwanf/gpt2-mini'),
    AutoTokenizer.from_pretrained('erwanf/gpt2-mini')
)
model = OutlinesModel(outlines_model)

```

As you already providing an Outlines model instance, there is no need to provide an `OutlinesProvider` yourself.
