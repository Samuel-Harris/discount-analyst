The `direct` module provides low-level methods for making imperative requests to LLMs where the only abstraction is input and output schema translation, enabling you to use all models with the same API.

These methods are thin wrappers around the Model implementations, offering a simpler interface when you don't need the full functionality of an Agent.

The following functions are available:

- model_request: Make a non-streamed async request to a model
- model_request_sync: Make a non-streamed synchronous request to a model
- model_request_stream: Make a streamed async request to a model
- model_request_stream_sync: Make a streamed sync request to a model
