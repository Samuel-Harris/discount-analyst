## Running the Example

With [dependencies installed and environment variables set](../setup/#usage), run:

```bash
python -m pydantic_ai_examples.pydantic_model

```

```bash
uv run -m pydantic_ai_examples.pydantic_model

```

This examples uses `openai:gpt-5` by default, but it works well with other models, e.g. you can run it with Gemini using:

```bash
PYDANTIC_AI_MODEL=gemini-2.5-pro python -m pydantic_ai_examples.pydantic_model

```

```bash
PYDANTIC_AI_MODEL=gemini-2.5-pro uv run -m pydantic_ai_examples.pydantic_model

```

(or `PYDANTIC_AI_MODEL=gemini-2.5-flash ...`)
