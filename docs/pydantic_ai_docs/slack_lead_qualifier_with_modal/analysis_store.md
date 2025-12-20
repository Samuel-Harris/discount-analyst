### Analysis store

The next building block we'll need is a place to store all the analyses that have been done so that we can look them up when we send the daily summary.

Fortunately, Modal provides us with a convenient way to store some data that can be read back in a subsequent Modal run (webhook or scheduled): [`modal.Dict`](https://modal.com/docs/reference/modal.Dict).

We define some convenience methods to easily add, list, and clear analyses.

[slack_lead_qualifier/store.py (L4-L31)](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/slack_lead_qualifier/store.py#L4-L31)

```python
...

import modal

...

class AnalysisStore:
    @classmethod
    @logfire.instrument('Add analysis to store')
    async def add(cls, analysis: Analysis):
        await cls._get_store().put.aio(analysis.profile.email, analysis.model_dump())

    @classmethod
    @logfire.instrument('List analyses from store')
    async def list(cls) -> list[Analysis]:
        return [
            Analysis.model_validate(analysis)
            async for analysis in cls._get_store().values.aio()
        ]

    @classmethod
    @logfire.instrument('Clear analyses from store')
    async def clear(cls):
        await cls._get_store().clear.aio()

    @classmethod
    def _get_store(cls) -> modal.Dict:
        return modal.Dict.from_name('analyses', create_if_missing=True)  # type: ignore

```

Note

Note that `# type: ignore` on the last line -- unfortunately `modal` does not fully define its types, so we need this to stop our static type checker `pyright`, which we run over all Pydantic AI code including examples, from complaining.
