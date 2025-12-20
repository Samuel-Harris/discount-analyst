If you're building a chat app or other interactive frontend for an AI agent, your backend will need to receive agent run input (like a chat message or complete [message history](../../message-history/)) from the frontend, and will need to stream the [agent's events](../../agents/#streaming-all-events) (like text, thinking, and tool calls) to the frontend so that the user knows what's happening in real time.

While your frontend could use Pydantic AI's ModelRequest and AgentStreamEvent directly, you'll typically want to use a UI event stream protocol that's natively supported by your frontend framework.

Pydantic AI natively supports two UI event stream protocols:

- [Agent-User Interaction (AG-UI) Protocol](../ag-ui/)
- [Vercel AI Data Stream Protocol](../vercel-ai/)

These integrations are implemented as subclasses of the abstract UIAdapter class, so they also serve as a reference for integrating with other UI event stream protocols.
