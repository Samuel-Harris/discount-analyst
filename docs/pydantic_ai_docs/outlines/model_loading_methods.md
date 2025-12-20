### Model Loading Methods

Alternatively, you can use some `OutlinesModel` class methods made to load a specific type of Outlines model directly. To do so, you must provide as arguments the same arguments you would have given to the associated Outlines model loading function (except in the case of SGLang).

There are methods for the 5 Outlines models that are officially supported in the integration into Pydantic AI:

- from_transformers
- from_llamacpp
- from_mlxlm
- from_sglang
- from_vllm_offline

#### Transformers

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

from pydantic_ai.models.outlines import OutlinesModel

model = OutlinesModel.from_transformers(
    AutoModelForCausalLM.from_pretrained('microsoft/Phi-3-mini-4k-instruct'),
    AutoTokenizer.from_pretrained('microsoft/Phi-3-mini-4k-instruct')
)

```

#### LlamaCpp

```python
from llama_cpp import Llama

from pydantic_ai.models.outlines import OutlinesModel

model = OutlinesModel.from_llamacpp(
    Llama.from_pretrained(
        repo_id='TheBloke/Mistral-7B-Instruct-v0.2-GGUF',
        filename='mistral-7b-instruct-v0.2.Q5_K_M.gguf',
    )
)

```

#### MLXLM

```python
from mlx_lm import load

from pydantic_ai.models.outlines import OutlinesModel

model = OutlinesModel.from_mlxlm(
    *load('mlx-community/TinyLlama-1.1B-Chat-v1.0-4bit')
)

```

#### SGLang

```python
from pydantic_ai.models.outlines import OutlinesModel

model = OutlinesModel.from_sglang(
    'http://localhost:11434',
    'api_key',
    'meta-llama/Llama-3.1-8B'
)

```

#### vLLM Offline

```python
from vllm import LLM

from pydantic_ai.models.outlines import OutlinesModel

model = OutlinesModel.from_vllm_offline(
    LLM('microsoft/Phi-3-mini-4k-instruct')
)

```
