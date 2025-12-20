### Running Examples

To run the examples (this will work whether you installed `pydantic_ai`, or cloned the repo), run:

```bash
python -m pydantic_ai_examples.<example_module_name>

```

```bash
uv run -m pydantic_ai_examples.<example_module_name>

```

For examples, to run the very simple [`pydantic_model`](../pydantic-model/) example:

```bash
python -m pydantic_ai_examples.pydantic_model

```

```bash
uv run -m pydantic_ai_examples.pydantic_model

```

If you like one-liners and you're using uv, you can run a pydantic-ai example with zero setup:

```bash
OPENAI_API_KEY='your-api-key' \
  uv run --with "pydantic-ai[examples]" \
  -m pydantic_ai_examples.pydantic_model

```

---

You'll probably want to edit examples in addition to just running them. You can copy the examples to a new directory with:

```bash
python -m pydantic_ai_examples --copy-to examples/

```

```bash
uv run -m pydantic_ai_examples --copy-to examples/

```
