agent = Agent('openai:gpt-5', toolsets=[restaurant_server])


async def main():
    """Run the agent to book a restaurant table."""
    result = await agent.run('Book me a table')
    print(f'\nResult: {result.output}')


if __name__ == '__main__':
    asyncio.run(main())

```
