Sometimes in an agent workflow, the agent does not need to know the exact tool output, but still needs to process the tool output in some ways. This is especially common in data analytics: the agent needs to know that the result of a query tool is a `DataFrame` with certain named columns, but not necessarily the content of every single row.

With Pydantic AI, you can use a [dependencies object](../../dependencies/) to store the result from one tool and use it in another tool.

In this example, we'll build an agent that analyzes the [Rotten Tomatoes movie review dataset from Cornell](https://huggingface.co/datasets/cornell-movie-review-data/rotten_tomatoes).

Demonstrates:

- [agent dependencies](../../dependencies/)
