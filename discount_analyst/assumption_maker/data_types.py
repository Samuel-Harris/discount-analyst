from pydantic import BaseModel


class SearchResult(BaseModel):
    response: str
    citations: list[str] | None = None
