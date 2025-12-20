Yes, I understand DuckDB SQL. DuckDB is an in-process analytical SQL database
that uses syntax similar to PostgreSQL. It specializes in analytical queries
and is designed for high-performance analysis of structured data.

Some key features of DuckDB SQL include:

 â€¢ OLAP (Online Analytical Processing) optimized
 â€¢ Columnar-vectorized query execution
 â€¢ Standard SQL support with PostgreSQL compatibility
 â€¢ Support for complex analytical queries
 â€¢ Efficient handling of CSV/Parquet/JSON files

I can help you with DuckDB SQL queries, schema design, optimization, or other
DuckDB-related questions.

```

Example of a multi-agent flow where one agent delegates work to another, then hands off control to a third agent.

Demonstrates:

- [agent delegation](../../multi-agent-applications/#agent-delegation)
- [programmatic agent hand-off](../../multi-agent-applications/#programmatic-agent-hand-off)
- [usage limits](../../agents/#usage-limits)

In this scenario, a group of agents work together to find the best flight for a user.

The control flow for this example can be summarised as follows:

```
graph TD
  START --> search_agent("search agent")
  search_agent --> extraction_agent("extraction agent")
  extraction_agent --> search_agent
  search_agent --> human_confirm("human confirm")
  human_confirm --> search_agent
  search_agent --> FAILED
  human_confirm --> find_seat_function("find seat function")
  find_seat_function --> human_seat_choice("human seat choice")
  human_seat_choice --> find_seat_agent("find seat agent")
  find_seat_agent --> find_seat_function
  find_seat_function --> buy_flights("buy flights")
  buy_flights --> SUCCESS
```
