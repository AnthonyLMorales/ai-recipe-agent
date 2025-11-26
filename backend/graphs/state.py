import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage


class CookingGraphState(TypedDict):
    # Conversation memory
    messages: Annotated[list[BaseMessage], operator.add]

    # Input
    query: str

    # Classification
    is_relevant: bool
    query_type: str | None
    dish: str | None
    ingredients: list[str] | None

    # Search decision and results
    needs_search: bool | None
    search_results: Annotated[list, operator.add]

    # Cookware
    required_cookware: list[str] | None
    can_cook: bool | None
    missing_cookware: list[str] | None

    # Output
    final_response: str
