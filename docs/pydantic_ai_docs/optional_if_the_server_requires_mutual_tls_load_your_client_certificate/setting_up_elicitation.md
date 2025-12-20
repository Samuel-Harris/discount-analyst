### Setting up Elicitation

To enable elicitation, provide an elicitation_callback function when creating your MCP server instance:

restaurant_server.py

```python
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP(name='Restaurant Booking')


class BookingDetails(BaseModel):
    """Schema for restaurant booking information."""

    restaurant: str = Field(description='Choose a restaurant')
    party_size: int = Field(description='Number of people', ge=1, le=8)
    date: str = Field(description='Reservation date (DD-MM-YYYY)')


@mcp.tool()
async def book_table(ctx: Context) -> str:
    """Book a restaurant table with user input."""
    # Ask user for booking details using Pydantic schema
    result = await ctx.elicit(message='Please provide your booking details:', schema=BookingDetails)

    if result.action == 'accept' and result.data:
        booking = result.data
        return f'âœ… Booked table for {booking.party_size} at {booking.restaurant} on {booking.date}'
    elif result.action == 'decline':
        return 'No problem! Maybe another time.'
    else:  # cancel
        return 'Booking cancelled.'


if __name__ == '__main__':
    mcp.run(transport='stdio')

```

This server demonstrates elicitation by requesting structured booking details from the client when the `book_table` tool is called. Here's how to create a client that handles these elicitation requests:

[Learn about Gateway](../../gateway) client_example.py

```python
import asyncio
from typing import Any

from mcp.client.session import ClientSession
from mcp.shared.context import RequestContext
from mcp.types import ElicitRequestParams, ElicitResult

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio


async def handle_elicitation(
    context: RequestContext[ClientSession, Any, Any],
    params: ElicitRequestParams,
) -> ElicitResult:
    """Handle elicitation requests from MCP server."""
    print(f'\n{params.message}')

    if not params.requestedSchema:
        response = input('Response: ')
        return ElicitResult(action='accept', content={'response': response})

    # Collect data for each field
    properties = params.requestedSchema['properties']
    data = {}

    for field, info in properties.items():
        description = info.get('description', field)

        value = input(f'{description}: ')

        # Convert to proper type based on JSON schema
        if info.get('type') == 'integer':
            data[field] = int(value)
        else:
            data[field] = value

    # Confirm
    confirm = input('\nConfirm booking? (y/n/c): ').lower()

    if confirm == 'y':
        print('Booking details:', data)
        return ElicitResult(action='accept', content=data)
    elif confirm == 'n':
        return ElicitResult(action='decline')
    else:
        return ElicitResult(action='cancel')
