### How Elicitation works

Elicitation introduces a new protocol message type called [`ElicitRequest`](https://modelcontextprotocol.io/specification/2025-06-18/schema#elicitrequest), which is sent from the server to the client when it needs additional information. The client can then respond with an [`ElicitResult`](https://modelcontextprotocol.io/specification/2025-06-18/schema#elicitresult) or an `ErrorData` message.

Here's a typical interaction:

- User makes a request to the MCP server (e.g. "Book a table at that Italian place")
- The server identifies that it needs more information (e.g. "Which Italian place?", "What date and time?")
- The server sends an `ElicitRequest` to the client asking for the missing information.
- The client receives the request, presents it to the user (e.g. via a terminal prompt, GUI dialog, or web interface).
- User provides the requested information, `decline` or `cancel` the request.
- The client sends an `ElicitResult` back to the server with the user's response.
- With the structured data, the server can continue processing the original request.

This allows for a more interactive and user-friendly experience, especially for multi-staged workflows. Instead of requiring all information upfront, the server can ask for it as needed, making the interaction feel more natural.
