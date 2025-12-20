## Document Input

Info

Some models do not support document input. Please check the model's documentation to confirm whether it supports document input.

You can provide document input using either DocumentUrl or BinaryContent. The process is similar to the examples above.

If you have a direct URL for the document, you can use DocumentUrl:

[Learn about Gateway](../gateway) document_input.py

```python
from pydantic_ai import Agent, DocumentUrl

agent = Agent(model='gateway/anthropic:claude-sonnet-4-5')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        DocumentUrl(url='https://storage.googleapis.com/cloud-samples-data/generative-ai/pdf/2403.05530.pdf'),
    ]
)
print(result.output)
#> This document is the technical report introducing Gemini 1.5, Google's latest large language model...

```

document_input.py

```python
from pydantic_ai import Agent, DocumentUrl

agent = Agent(model='anthropic:claude-sonnet-4-5')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        DocumentUrl(url='https://storage.googleapis.com/cloud-samples-data/generative-ai/pdf/2403.05530.pdf'),
    ]
)
print(result.output)
#> This document is the technical report introducing Gemini 1.5, Google's latest large language model...

```

The supported document formats vary by model.

You can also use BinaryContent to pass document data directly:

[Learn about Gateway](../gateway) binary_content_input.py

```python
from pathlib import Path
from pydantic_ai import Agent, BinaryContent

pdf_path = Path('document.pdf')
agent = Agent(model='gateway/anthropic:claude-sonnet-4-5')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        BinaryContent(data=pdf_path.read_bytes(), media_type='application/pdf'),
    ]
)
print(result.output)
#> The document discusses...

```

binary_content_input.py

```python
from pathlib import Path
from pydantic_ai import Agent, BinaryContent

pdf_path = Path('document.pdf')
agent = Agent(model='anthropic:claude-sonnet-4-5')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        BinaryContent(data=pdf_path.read_bytes(), media_type='application/pdf'),
    ]
)
print(result.output)
#> The document discusses...

```
