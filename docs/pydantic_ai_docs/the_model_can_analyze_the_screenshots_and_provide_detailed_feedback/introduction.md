```

- **`return_value`**: The actual return value used in the tool response. This is what gets serialized and sent back to the model as the tool's result.
- **`content`**: A sequence of content (text, images, documents, etc.) that provides additional context to the model. This appears as a separate user message.
- **`metadata`**: Optional metadata that your application can access but is not sent to the LLM. Useful for logging, debugging, or additional processing. Some other AI frameworks call this feature "artifacts".

This separation allows you to provide rich context to the model while maintaining clean, structured return values for your application logic.
