### Web app

As it stands, neither of these functions are actually being called from anywhere.

Let's implement a [FastAPI](https://fastapi.tiangolo.com/) endpoint to handle the `team_join` Slack webhook (also known as the [Slack Events API](https://docs.slack.dev/apis/events-api)) and call the [`process_slack_member`](#process_slack_member) function we just defined. We also instrument FastAPI using Logfire for good measure.

[slack_lead_qualifier/app.py (L20-L36)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/app.py#L20-L36)

```python
...

app = FastAPI()
logfire.instrument_fastapi(app, capture_headers=True)


@app.post('/')
async def process_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    if payload['type'] == 'url_verification':
        return {'challenge': payload['challenge']}
    elif (
        payload['type'] == 'event_callback' and payload['event']['type'] == 'team_join'
    ):
        profile = Profile.model_validate(payload['event']['user']['profile'])

        process_slack_member(profile)
        return {'status': 'OK'}

    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

```

#### `process_slack_member` with Modal

I was a little sneaky there -- we're not actually calling the [`process_slack_member`](#process_slack_member) function we defined in `functions.py` directly, as Slack requires webhooks to respond within 3 seconds, and we need a bit more time than that to talk to the LLM, do some web searches, and send the Slack message.

Instead, we're calling the following function defined alongside the app, which uses Modal's [`modal.Function.spawn`](https://modal.com/docs/reference/modal.Function#spawn) feature to run a function in the background. (If you're curious what the Modal side of this function looks like, you can [jump ahead](#backgrounded-process_slack_member).)

Because `modal.py` (which we'll see in the next section) imports `app.py`, we import from `modal.py` inside the function definition because doing so at the top level would have resulted in a circular import error.

We also pass along the current Logfire context to get [Distributed Tracing](https://logfire.pydantic.dev/docs/how-to-guides/distributed-tracing/), meaning that the background function execution will show up nested under the webhook request trace, so that we have everything related to that request in one place.

[slack_lead_qualifier/app.py (L11-L16)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/app.py#L11-L16)

```python
...

def process_slack_member(profile: Profile):
    from .modal import process_slack_member as _process_slack_member

    _process_slack_member.spawn(
        profile.model_dump(), logfire_ctx=get_context()
    )

...

```
