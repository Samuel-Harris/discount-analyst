message_history: list[ModelMessage] = [
    ModelRequest([UserPromptPart(content='What is 2+2?')]),
    ModelResponse([TextPart(content='2+2 equals 4.')])
]
