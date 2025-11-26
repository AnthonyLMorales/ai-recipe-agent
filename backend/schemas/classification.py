from pydantic import BaseModel, Field


class ClassificationOutput(BaseModel):
    """Output schema for query classification."""

    relevant: bool
    query_type: str | None
    dish: str | None
    ingredients: list[str] | None
    required_cookware: list[str] | None = Field(
        default=None, description="List of cookware/tools required for this recipe"
    )
    reason: str | None
