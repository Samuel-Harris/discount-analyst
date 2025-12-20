### Models

#### `Profile`

First, we define a [Pydantic](https://docs.pydantic.dev) model that represents a Slack user profile. These are the fields we get from the [`team_join`](https://docs.slack.dev/reference/events/team_join) event that's sent to the webhook endpoint that we'll define in a bit.

[slack_lead_qualifier/models.py (L11-L15)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/models.py#L11-L15)

```python
...

class Profile(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    email: str

...

```

We also define a `Profile.as_prompt()` helper method that uses format_as_xml to turn the profile into a string that can be sent to the model.

[slack_lead_qualifier/models.py (L7-L19)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/models.py#L7-L19)

```python
...

from pydantic_ai import format_as_xml

...

class Profile(BaseModel):

...

    def as_prompt(self) -> str:
        return format_as_xml(self, root_tag='profile')

...

```

#### `Analysis`

The second model we'll need represents the result of the analysis that the agent will perform. We include docstrings to provide additional context to the model on what these fields should contain.

[slack_lead_qualifier/models.py (L23-L31)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/models.py#L23-L31)

```python
...

class Analysis(BaseModel):
    profile: Profile
    organization_name: str
    organization_domain: str
    job_title: str
    relevance: Annotated[int, Ge(1), Le(5)]
    """Estimated fit for Pydantic Logfire: 1 = low, 5 = high"""
    summary: str
    """One-sentence welcome note summarising who they are and how we might help"""

...

```

We also define a `Analysis.as_slack_blocks()` helper method that turns the analysis into some [Slack blocks](https://api.slack.com/reference/block-kit/blocks) that can be sent to the Slack API to post a new message.

[slack_lead_qualifier/models.py (L23-L46)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/models.py#L23-L46)

```python
...

class Analysis(BaseModel):

...

    def as_slack_blocks(self, include_relevance: bool = False) -> list[dict[str, Any]]:
        profile = self.profile
        relevance = f'({self.relevance}/5)' if include_relevance else ''
        return [
            {
                'type': 'markdown',
                'text': f'[{profile.display_name}](mailto:{profile.email}), {self.job_title} at [**{self.organization_name}**](https://{self.organization_domain}) {relevance}',
            },
            {
                'type': 'markdown',
                'text': self.summary,
            },
        ]

```
