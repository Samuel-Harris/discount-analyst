### `RuntimeError: This event loop is already running`

This error is caused by conflicts between the event loops in Jupyter notebook and Pydantic AI's. One way to manage these conflicts is by using [`nest-asyncio`](https://pypi.org/project/nest-asyncio/). Namely, before you execute any agent runs, do the following:

```python
import nest_asyncio

nest_asyncio.apply()

```

Note: This fix also applies to Google Colab and [Marimo](https://github.com/marimo-team/marimo).
