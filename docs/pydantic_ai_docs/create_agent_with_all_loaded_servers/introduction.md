agent = Agent('openai:gpt-5', toolsets=servers)

async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)

```

_(This example is complete, it can be run "as is" â€” you'll need to add `asyncio.run(main())` to run `main`)_
