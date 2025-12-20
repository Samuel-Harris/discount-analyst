### Slack app

You need to have a Slack workspace and the necessary permissions to create apps.

2. Create a new Slack app using the instructions at <https://docs.slack.dev/quickstart>.

   1. In step 2, "Requesting scopes", request the following scopes:
      - [`users.read`](https://docs.slack.dev/reference/scopes/users.read)
      - [`users.read.email`](https://docs.slack.dev/reference/scopes/users.read.email)
      - [`users.profile.read`](https://docs.slack.dev/reference/scopes/users.profile.read)
   1. In step 3, "Installing and authorizing the app", note down the Access Token as we're going to need to store it as a Secret in Modal.
   1. You can skip steps 4 and 5. We're going to need to subscribe to the `team_join` event, but at this point you don't have a webhook URL yet.

1. Create the channels the app will post into, and add the Slack app to them:

   - `#new-slack-leads`
   - `#daily-slack-leads-summary`

   These names are hard-coded in the example. If you want to use different channels, you can clone the repo and change them in `examples/pydantic_examples/slack_lead_qualifier/functions.py`.
