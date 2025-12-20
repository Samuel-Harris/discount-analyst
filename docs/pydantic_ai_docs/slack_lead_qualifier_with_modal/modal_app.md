### Modal app

Now let's see how easy Modal makes it to deploy all of this.

#### Set up Modal

The first thing we do is define the Modal app, by specifying the base image to use (Debian with Python 3.13), all the Python packages it needs, and all of the secrets defined in the Modal interface that need to be made available during runtime.

[slack_lead_qualifier/modal.py (L4-L21)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/modal.py#L4-L21)

```python
...

import modal

image = modal.Image.debian_slim(python_version='3.13').pip_install(
    'pydantic',
    'pydantic_ai_slim[openai,duckduckgo]',
    'logfire[httpx,fastapi]',
    'fastapi[standard]',
    'httpx',
)
app = modal.App(
    name='slack-lead-qualifier',
    image=image,
    secrets=[
        modal.Secret.from_name('logfire'),
        modal.Secret.from_name('openai'),
        modal.Secret.from_name('slack'),
    ],
)

...

```

#### Set up Logfire

Next, we define a function to set up Logfire instrumentation for Pydantic AI and HTTPX.

We cannot do this at the top level of the file, as the requested packages (like `logfire`) will only be available within functions running on Modal (like the ones we'll define next). This file, `modal.py`, runs on your local machine and only has access to the `modal` package.

[slack_lead_qualifier/modal.py (L25-L30)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/modal.py#L25-L30)

```python
...

def setup_logfire():
    import logfire

    logfire.configure(service_name=app.name)
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)

...

```

#### Web app

To deploy a [web endpoint](https://modal.com/docs/guide/webhooks) on Modal, we simply define a function that returns an ASGI app (like FastAPI) and decorate it with `@app.function()` and `@modal.asgi_app()`.

This `web_app` function will be run on Modal, so inside the function we can call the `setup_logfire` function that requires the `logfire` package, and import `app.py` which uses the other requested packages.

By default, Modal spins up a container to handle a function call (like a web request) on-demand, meaning there's a little bit of startup time to each request. However, Slack requires webhooks to respond within 3 seconds, so we specify `min_containers=1` to keep the web endpoint running and ready to answer requests at all times. This is a bit annoying and wasteful, but fortunately [Modal's pricing](https://modal.com/pricing) is pretty reasonable, you get $30 free monthly compute, and they offer up to $50k in free credits for startup and academic researchers.

[slack_lead_qualifier/modal.py (L34-L41)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/modal.py#L34-L41)

```python
...

@app.function(min_containers=1)
@modal.asgi_app()  # type: ignore
def web_app():
    setup_logfire()

    from .app import app as _app

    return _app

...

```

Note

Note that `# type: ignore` on the `@modal.asgi_app()` line -- unfortunately `modal` does not fully define its types, so we need this to stop our static type checker `pyright`, which we run over all Pydantic AI code including examples, from complaining.

#### Scheduled `send_daily_summary`

To define a [scheduled function](https://modal.com/docs/guide/cron), we can use the `@app.function()` decorator with a `schedule` argument. This Modal function will call our imported [`send_daily_summary`](#send_daily_summary) function every day at 8 am UTC.

[slack_lead_qualifier/modal.py (L60-L66)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/modal.py#L60-L66)

```python
...

@app.function(schedule=modal.Cron('0 8 * * *'))  # Every day at 8am UTC
async def send_daily_summary():
    setup_logfire()

    from .functions import send_daily_summary as _send_daily_summary

    await _send_daily_summary()

```

#### Backgrounded `process_slack_member`

Finally, we define a Modal function that wraps our [`process_slack_member`](#process_slack_member) function, so that it can run in the background.

As you'll remember from when we [spawned this function from the web app](#process_slack_member-with-modal), we passed along the Logfire context to get [Distributed Tracing](https://logfire.pydantic.dev/docs/how-to-guides/distributed-tracing/), so we need to attach it here.

[slack_lead_qualifier/modal.py (L45-L56)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/modal.py#L45-L56)

```python
...

@app.function()
async def process_slack_member(profile_raw: dict[str, Any], logfire_ctx: Any):
    setup_logfire()

    from logfire.propagate import attach_context

    from .functions import process_slack_member as _process_slack_member
    from .models import Profile

    with attach_context(logfire_ctx):
        profile = Profile.model_validate(profile_raw)
        await _process_slack_member(profile)

...

```
