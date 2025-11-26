import uuid

from pydantic import BaseModel, Field


class QueryInput(BaseModel):
    """Input schema for cooking query requests."""

    query: str
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class QueryResponse(BaseModel):
    """Response schema for cooking query responses."""

    response: str
    metadata: dict = {}
    thread_id: str
