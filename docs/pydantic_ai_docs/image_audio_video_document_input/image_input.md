## Image Input

Info

Some models do not support image input. Please check the model's documentation to confirm whether it supports image input.

If you have a direct URL for the image, you can use ImageUrl:

[Learn about Gateway](../gateway) image_input.py

```python
from pydantic_ai import Agent, ImageUrl

agent = Agent(model='gateway/openai:gpt-5')
result = agent.run_sync(
    [
        'What company is this logo from?',
        ImageUrl(url='https://iili.io/3Hs4FMg.png'),
    ]
)
print(result.output)
#> This is the logo for Pydantic, a data validation and settings management library in Python.

```

image_input.py

```python
from pydantic_ai import Agent, ImageUrl

agent = Agent(model='openai:gpt-5')
result = agent.run_sync(
    [
        'What company is this logo from?',
        ImageUrl(url='https://iili.io/3Hs4FMg.png'),
    ]
)
print(result.output)
#> This is the logo for Pydantic, a data validation and settings management library in Python.

```

If you have the image locally, you can also use BinaryContent:

[Learn about Gateway](../gateway) local_image_input.py

```python
import httpx

from pydantic_ai import Agent, BinaryContent

image_response = httpx.get('https://iili.io/3Hs4FMg.png')  # Pydantic logo

agent = Agent(model='gateway/openai:gpt-5')
result = agent.run_sync(
    [
        'What company is this logo from?',
        BinaryContent(data=image_response.content, media_type='image/png'),  # (1)!
    ]
)
print(result.output)
#> This is the logo for Pydantic, a data validation and settings management library in Python.

```

1. To ensure the example is runnable we download this image from the web, but you can also use `Path().read_bytes()` to read a local file's contents.

local_image_input.py

```python
import httpx

from pydantic_ai import Agent, BinaryContent

image_response = httpx.get('https://iili.io/3Hs4FMg.png')  # Pydantic logo

agent = Agent(model='openai:gpt-5')
result = agent.run_sync(
    [
        'What company is this logo from?',
        BinaryContent(data=image_response.content, media_type='image/png'),  # (1)!
    ]
)
print(result.output)
#> This is the logo for Pydantic, a data validation and settings management library in Python.

```

1. To ensure the example is runnable we download this image from the web, but you can also use `Path().read_bytes()` to read a local file's contents.
