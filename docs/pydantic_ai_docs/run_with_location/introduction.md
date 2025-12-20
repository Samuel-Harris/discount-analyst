result = agent.run_sync(
    'What is the weather like?',
    deps={'location': 'London'},
)
print(result.output)
#> It's currently raining in London.
