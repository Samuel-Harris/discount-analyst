In this example, we're going to build an agentic app that:

- automatically researches each new member that joins a company's public Slack community to see how good of a fit they are for the company's commercial product,
- sends this analysis into a (private) Slack channel, and
- sends a daily summary of the top 5 leads from the previous 24 hours into a (different) Slack channel.

We'll be deploying the app on [Modal](https://modal.com), as it lets you use Python to define an app with web endpoints, scheduled functions, and background functions, and deploy them with a CLI, without needing to set up or manage any infrastructure. It's a great way to lower the barrier for people in your organization to start building and deploying AI agents to make their jobs easier.

We also add [Pydantic Logfire](https://pydantic.dev/logfire) to get observability into the app and agent as they're running in response to webhooks and the schedule
