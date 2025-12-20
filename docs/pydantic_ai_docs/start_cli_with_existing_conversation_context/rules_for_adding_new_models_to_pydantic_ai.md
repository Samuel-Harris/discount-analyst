## Rules for adding new models to Pydantic AI

To avoid an excessive workload for the maintainers of Pydantic AI, we can't accept all model contributions, so we're setting the following rules for when we'll accept new models and when we won't. This should hopefully reduce the chances of disappointment and wasted work.

- To add a new model with an extra dependency, that dependency needs > 500k monthly downloads from PyPI consistently over 3 months or more
- To add a new model which uses another models logic internally and has no extra dependencies, that model's GitHub org needs > 20k stars in total
- For any other model that's just a custom URL and API key, we're happy to add a one-paragraph description with a link and instructions on the URL to use
- For any other model that requires more logic, we recommend you release your own Python package `pydantic-ai-xxx`, which depends on [`pydantic-ai-slim`](../install/#slim-install) and implements a model that inherits from our Model ABC

If you're unsure about adding a model, please [create an issue](https://github.com/pydantic/pydantic-ai/issues).
