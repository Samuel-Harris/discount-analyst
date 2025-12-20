## Usage

The VercelAIAdapter class is responsible for transforming agent run input received from the frontend into arguments for [`Agent.run_stream_events()`](../../agents/#running-agents), running the agent, and then transforming Pydantic AI events into Vercel AI events. The event stream transformation is handled by the VercelAIEventStream class, but you typically won't use this directly.

If you're using a Starlette-based web framework like FastAPI, you can use the VercelAIAdapter.dispatch_request() class method from an endpoint function to directly handle a request and return a streaming response of Vercel AI events. This is demonstrated in the next section.

If you're using a web framework not based on Starlette (e.g. Django or Flask) or need fine-grained control over the input or output, you can create a `VercelAIAdapter` instance and directly use its methods. This is demonstrated in "Advanced Usage" section below.
