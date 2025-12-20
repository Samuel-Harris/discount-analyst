summarize_agent = Agent(
    'openai:gpt-5-mini',
    instructions="""
Summarize this conversation, omitting small talk and unrelated topics.
Focus on the technical discussion and next steps.
""",
)


async def summarize_old_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    # Summarize the oldest 10 messages
    if len(messages) > 10:
        oldest_messages = messages[:10]
        summary = await summarize_agent.run(message_history=oldest_messages)
        # Return the last message and the summary
        return summary.new_messages() + messages[-1:]

    return messages


agent = Agent('openai:gpt-5', history_processors=[summarize_old_messages])

```

Be careful when summarizing the message history

When summarizing the message history, you need to make sure that tool calls and returns are paired, otherwise the LLM may return an error. For more details, refer to [this GitHub issue](https://github.com/pydantic/pydantic-ai/issues/2050#issuecomment-3019976269), where you can find examples of summarizing the message history.
