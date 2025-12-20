client = create_retrying_client()
model = OpenAIChatModel('gpt-5', provider=OpenAIProvider(http_client=client))
agent = Agent(model)

```
