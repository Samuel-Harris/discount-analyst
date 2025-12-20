### Send Slack message

Next, we'll need a way to actually send a Slack message, so we define a simple function that uses Slack's [`chat.postMessage`](https://api.slack.com/methods/chat.postMessage) API.

[slack_lead_qualifier/slack.py (L8-L30)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/slack.py#L8-L30)

```python
...

API_KEY = os.getenv('SLACK_API_KEY')
assert API_KEY, 'SLACK_API_KEY is not set'


@logfire.instrument('Send Slack message')
async def send_slack_message(channel: str, blocks: list[dict[str, Any]]):
    client = httpx.AsyncClient()
    response = await client.post(
        'https://slack.com/api/chat.postMessage',
        json={
            'channel': channel,
            'blocks': blocks,
        },
        headers={
            'Authorization': f'Bearer {API_KEY}',
        },
        timeout=5,
    )
    response.raise_for_status()
    result = response.json()
    if not result.get('ok', False):
        error = result.get('error', 'Unknown error')
        raise Exception(f'Failed to send to Slack: {error}')

```
