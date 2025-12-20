### UserError

Bases: `RuntimeError`

Error caused by a usage mistake by the application developer â€” You!

Source code in `pydantic_ai_slim/pydantic_ai/exceptions.py`

```python
class UserError(RuntimeError):
    """Error caused by a usage mistake by the application developer â€” You!"""

    message: str
    """Description of the mistake."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

```

#### message

```python
message: str = message

```

Description of the mistake.
