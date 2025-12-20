## Uploaded Files

Some model providers like Google's Gemini API support [uploading files](https://ai.google.dev/gemini-api/docs/files). You can upload a file to the model API using the client you can get from the provider and use the resulting URL as input:

file_upload.py

```python
from pydantic_ai import Agent, DocumentUrl
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

provider = GoogleProvider()
file = provider.client.files.upload(file='pydantic-ai-logo.png')
assert file.uri is not None

agent = Agent(GoogleModel('gemini-2.5-flash', provider=provider))
result = agent.run_sync(
    [
        'What company is this logo from?',
        DocumentUrl(url=file.uri, media_type=file.mime_type),
    ]
)
print(result.output)

```
