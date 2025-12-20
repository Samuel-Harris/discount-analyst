### Instructions Functions, Output Functions, and History Processors

Pydantic AI runs non-async [instructions](../../agents/#instructions) and [system prompt](../../agents/#system-prompts) functions, [history processors](../../message-history/#processing-message-history), [output functions](../../output/#output-functions), and [output validators](../../output/#output-validator-functions) in threads, which are not supported inside Temporal workflows and require an activity. Ensure that these functions are async instead.

Synchronous tool functions are supported, as tools are automatically run in activities unless this is [explicitly disabled](#activity-configuration). Still, it's recommended to make tool functions async as well to improve performance.
