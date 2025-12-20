### UnexpectedResponseError

Bases: `Exception`

An error raised when an unexpected response is received from the server.

Source code in `.venv/lib/python3.12/site-packages/fasta2a/client.py`

```python
class UnexpectedResponseError(Exception):
    """An error raised when an unexpected response is received from the server."""

    def __init__(self, status_code: int, content: str) -> None:
        self.status_code = status_code
        self.content = content

```
