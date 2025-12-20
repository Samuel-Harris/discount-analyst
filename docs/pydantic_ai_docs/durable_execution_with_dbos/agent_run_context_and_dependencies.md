### Agent Run Context and Dependencies

DBOS checkpoints workflow inputs/outputs and step outputs into a database using [`pickle`](https://docs.python.org/3/library/pickle.html). This means you need to make sure [dependencies](../../dependencies/) object provided to DBOSAgent.run() or DBOSAgent.run_sync(), and tool outputs can be serialized using pickle. You may also want to keep the inputs and outputs small (under ~2 MB). PostgreSQL and SQLite support up to 1 GB per field, but large objects may impact performance.
