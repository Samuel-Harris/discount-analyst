### Features

Now we can start putting these building blocks together to implement the actual features we want!

#### `process_slack_member`

This function takes a [`Profile`](#profile), [analyzes](#analyze_profile) it using the agent, adds it to the [`AnalysisStore`](#analysis-store), and [sends](#send-slack-message) the analysis into the `#new-slack-leads` channel.

[slack_lead_qualifier/functions.py (L4-L45)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/functions.py#L4-L45)

```python
...

from .agent import analyze_profile
from .models import Profile

from .slack import send_slack_message
from .store import AnalysisStore

...

NEW_LEAD_CHANNEL = '#new-slack-leads'

...

@logfire.instrument('Process Slack member')
async def process_slack_member(profile: Profile):
    analysis = await analyze_profile(profile)
    logfire.info('Analysis', analysis=analysis)

    if analysis is None:
        return

    await AnalysisStore().add(analysis)

    await send_slack_message(
        NEW_LEAD_CHANNEL,
        [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': f'New Slack member with score {analysis.relevance}/5',
                },
            },
            {
                'type': 'divider',
            },
            *analysis.as_slack_blocks(),
        ],
    )

...

```

#### `send_daily_summary`

This function list all of the analyses in the [`AnalysisStore`](#analysis-store), takes the top 5 by relevance, [sends](#send-slack-message) them into the `#daily-slack-leads-summary` channel, and clears the `AnalysisStore` so that the next daily run won't process these analyses again.

[slack_lead_qualifier/functions.py (L8-L85)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/functions.py#L8-L85)

```python
...

from .slack import send_slack_message
from .store import AnalysisStore

...

DAILY_SUMMARY_CHANNEL = '#daily-slack-leads-summary'

...

@logfire.instrument('Send daily summary')
async def send_daily_summary():
    analyses = await AnalysisStore().list()
    logfire.info('Analyses', analyses=analyses)

    if len(analyses) == 0:
        return

    sorted_analyses = sorted(analyses, key=lambda x: x.relevance, reverse=True)
    top_analyses = sorted_analyses[:5]

    blocks = [
        {
            'type': 'header',
            'text': {
                'type': 'plain_text',
                'text': f'Top {len(top_analyses)} new Slack members from the last 24 hours',
            },
        },
    ]

    for analysis in top_analyses:
        blocks.extend(
            [
                {
                    'type': 'divider',
                },
                *analysis.as_slack_blocks(include_relevance=True),
            ]
        )

    await send_slack_message(
        DAILY_SUMMARY_CHANNEL,
        blocks,
    )

    await AnalysisStore().clear()

```
