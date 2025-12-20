Simple chat app example build with FastAPI.

Demonstrates:

- [reusing chat history](../../message-history/)
- [serializing messages](../../message-history/#accessing-messages-from-results)
- [streaming responses](../../output/#streamed-results)

This demonstrates storing chat history between requests and using it to give the model context for new responses.

Most of the complex logic here is between `chat_app.py` which streams the response to the browser, and `chat_app.ts` which renders messages in the browser.
