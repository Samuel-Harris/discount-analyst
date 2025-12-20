Pydantic AI uses a dependency injection system to provide data and services to your agent's [system prompts](../agents/#system-prompts), [tools](../tools/) and [output validators](../output/#output-validator-functions).

Matching Pydantic AI's design philosophy, our dependency system tries to use existing best practice in Python development rather than inventing esoteric "magic", this should make dependencies type-safe, understandable, easier to test, and ultimately easier to deploy in production.
