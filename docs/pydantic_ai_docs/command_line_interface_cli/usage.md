## Usage

You'll need to set an environment variable depending on the provider you intend to use.

E.g. if you're using OpenAI, set the `OPENAI_API_KEY` environment variable:

```bash
export OPENAI_API_KEY='your-api-key-here'

```

Then with [`uvx`](https://docs.astral.sh/uv/guides/tools/), run:

```bash
uvx clai

```

Or to install `clai` globally [with `uv`](https://docs.astral.sh/uv/guides/tools/#installing-tools), run:

```bash
uv tool install clai
...
clai

```

Or with `pip`, run:

```bash
pip install clai
...
clai

```

Either way, running `clai` will start an interactive session where you can chat with the AI model. Special commands available in interactive mode:

- `/exit`: Exit the session
- `/markdown`: Show the last response in markdown format
- `/multiline`: Toggle multiline input mode (use Ctrl+D to submit)
- `/cp`: Copy the last response to clipboard
