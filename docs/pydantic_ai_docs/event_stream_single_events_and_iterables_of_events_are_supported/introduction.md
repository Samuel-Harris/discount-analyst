@agent.tool_plain
async def document_predict_state() -> list[CustomEvent]:
    """Enable document state prediction.

    Returns:
        CustomEvent containing the event to enable state prediction.
    """
    return [
        CustomEvent(
            type=EventType.CUSTOM,
            name='PredictState',
            value=[
                {
                    'state_key': 'document',
                    'tool': 'write_document',
                    'tool_argument': 'document',
                },
            ],
        ),
    ]


@agent.instructions()
async def story_instructions(ctx: RunContext[StateDeps[DocumentState]]) -> str:
    """Provide instructions for writing document if present.

    Args:
        ctx: The run context containing document state information.

    Returns:
        Instructions string for the document writing agent.
    """
    return dedent(
        f"""You are a helpful assistant for writing documents.

        Before you start writing, you MUST call the `document_predict_state`
        tool to enable state prediction.

        To present the document to the user for review, you MUST use the
        `write_document` tool.

        When you have written the document, DO NOT repeat it as a message.
        If accepted briefly summarize the changes you made, 2 sentences
        max, otherwise ask the user to clarify what they want to change.

        This is the current document:

        {ctx.deps.state.document}
        """
    )


app = AGUIApp(agent, deps=StateDeps(DocumentState()))

```
