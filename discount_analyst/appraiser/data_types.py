from pydantic import BaseModel


class SearchResult(BaseModel):
    response: str
