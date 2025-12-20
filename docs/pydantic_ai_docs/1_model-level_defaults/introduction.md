model = OpenAIChatModel(
    'gpt-5',
    settings=ModelSettings(temperature=0.8, max_tokens=500)  # Base defaults
)
