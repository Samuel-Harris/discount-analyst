## Usage

1. Make sure you have the [dependencies installed](../setup/#usage).

1. Authenticate with Modal:

   ```bash
   python/uv-run -m modal setup

   ```

1. Run the example as an [ephemeral Modal app](https://modal.com/docs/guide/apps#ephemeral-apps), meaning it will only run until you quit it using Ctrl+C:

   ```bash
   python/uv-run -m modal serve -m pydantic_ai_examples.slack_lead_qualifier.modal

   ```

1. Note down the URL after `Created web function web_app =>`, this is your webhook endpoint URL.

1. Go back to <https://docs.slack.dev/quickstart> and follow step 4, "Configuring the app for event listening", to subscribe to the `team_join` event with the webhook endpoint URL you noted down as the Request URL.

Now when someone new (possibly you with a throwaway email) joins the Slack workspace, you'll see the webhook event being processed in the terminal where you ran `modal serve` and in the Logfire Live view, and after waiting a few seconds you should see the result appear in the `#new-slack-leads` Slack channel!

Faking a Slack signup

You can also fake a Slack signup event and try out the agent like this, with any name or email you please:

```bash
curl -X POST <webhook endpoint URL> \
-H "Content-Type: application/json" \
-d '{
    "type": "event_callback",
    "event": {
        "type": "team_join",
        "user": {
            "profile": {
                "email": "samuel@pydantic.dev",
                "first_name": "Samuel",
                "last_name": "Colvin",
                "display_name": "Samuel Colvin"
            }
        }
    }
}'

```

Deploying to production

If you'd like to deploy this app into your Modal workspace in a persistent fashion, you can use this command:

```bash
python/uv-run -m modal deploy -m pydantic_ai_examples.slack_lead_qualifier.modal

```

You'll likely want to [download the code](https://github.com/pydantic/pydantic-ai/tree/main/examples/pydantic_ai_examples/slack_lead_qualifier) first, put it in a new repo, and then do [continuous deployment](https://modal.com/docs/guide/continuous-deployment#github-actions) using GitHub Actions.

Don't forget to update the Slack event request URL to the new persistent URL! You'll also want to modify the [instructions for the agent](#agent) to your own situation.
