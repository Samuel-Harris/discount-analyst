## Processing Message History

Sometimes you may want to modify the message history before it's sent to the model. This could be for privacy reasons (filtering out sensitive information), to save costs on tokens, to give less context to the LLM, or custom processing logic.

Pydantic AI provides a `history_processors` parameter on `Agent` that allows you to intercept and modify the message history before each model request.

History processors replace the message history

History processors replace the message history in the state with the processed messages, including the new user prompt part. This means that if you want to keep the original message history, you need to make a copy of it.
