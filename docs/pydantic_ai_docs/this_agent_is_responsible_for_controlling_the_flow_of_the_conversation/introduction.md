search_agent = Agent[Deps, FlightDetails | NoFlightFound](
    'openai:gpt-5',
    output_type=FlightDetails | NoFlightFound,  # type: ignore
    retries=4,
    system_prompt=(
        'Your job is to find the cheapest flight for the user on the given date. '
    ),
)
