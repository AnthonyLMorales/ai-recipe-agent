import logging

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from constants.constants import AVAILABLE_COOKWARE
from schemas.classification import ClassificationOutput
from tools import tavily_search_tool

from .state import CookingGraphState

logger = logging.getLogger(__name__)


def classifier_node(state: CookingGraphState) -> dict:
    """
    This node classifies the user query using conversation context.

    INPUT: Reads state["query"] and state["messages"]
    OUTPUT: Returns dict with classification fields and updated messages
    """
    logger.info(f"CLASSIFIER NODE: Processing query: {state['query']}")

    # Your existing classifier logic
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = PydanticOutputParser(pydantic_object=ClassificationOutput)

    # Build context from message history (last 6 messages)
    conversation_context = ""
    if state.get("messages"):
        recent_messages = state["messages"][-6:]
        conversation_context = "\n\nRecent Conversation:\n"
        for msg in recent_messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            conversation_context += f"{role}: {msg.content}\n"

    prompt = ChatPromptTemplate.from_template("""
        You are a cooking-domain classifier.

        {conversation_context}

        Current User Query: {query}

        Use the conversation history to understand context. Examples:
        - If user asked "How do I make pasta?" and now asks "What about gluten-free?",
          recognize they're asking about gluten-free pasta.
        - If they asked about a dish and now ask "What cookware?", know they mean that dish.

        Your tasks:
        1. Determine if the query is cooking / recipe related (considering context).
        2. If not relevant: return relevant=false and query_type="irrelevant".
        3. If relevant: classify it into EXACTLY ONE of:
           - "general_cooking": asking about methods, cooking techniques, food science.
           - "recipe_request": asking for a recipe for a specific dish.
           - "ingredient_query": user provides ingredients and asks what they can make.

        4. Extract required fields:
           - For recipe_request: identify the dish name and required cookware/tools.
           - For ingredient_query: list ingredients only as nouns and required cookware/tools.
           - For required_cookware: list common cookware items like "Frying Pan", "Knife", "Whisk", "Pot", "Stovetop", "Spatula", "Spoon", "Ladle", etc.

        Respond ONLY in JSON matching the schema.

        {format_instructions}
    """)

    chain = prompt | llm | parser

    result = chain.invoke(
        {
            "query": state["query"],
            "conversation_context": conversation_context,
            "format_instructions": parser.get_format_instructions(),
        }
    )

    # Add current query to message history
    messages_update = [HumanMessage(content=state["query"])]

    # Return fields to UPDATE the state
    return {
        "is_relevant": result.relevant,
        "query_type": result.query_type,
        "dish": result.dish,
        "ingredients": result.ingredients,
        "required_cookware": result.required_cookware,
        "messages": messages_update,
    }


def decide_search_node(state: CookingGraphState) -> dict:
    """
    This node decides whether a web search is needed.

    INPUT: Reads state["query_type"], state["dish"], state["ingredients"]
    OUTPUT: Returns dict with needs_search boolean
    """
    logger.info(f"DECIDE SEARCH NODE: Query type: {state.get('query_type')}")

    query_type = state.get("query_type", "")

    # Typically need search for specific recipes or ingredient-based queries
    needs_search = query_type in ["recipe_request", "ingredient_query"]

    logger.debug(f"Search decision result: needs_search={needs_search}")

    return {"needs_search": needs_search}


def search_node(state: CookingGraphState) -> dict:
    """
    This node performs web search using Tavily.

    INPUT: Reads state["query"], state["dish"], state["ingredients"]
    OUTPUT: Returns dict with search_results
    """
    logger.info("SEARCH NODE: Performing web search")

    # Build search query based on query type
    query_type = state.get("query_type", "")

    if query_type == "recipe_request" and state.get("dish"):
        search_query = f"recipe for {state['dish']}"
    elif query_type == "ingredient_query" and state.get("ingredients"):
        ingredients_str = ", ".join(state["ingredients"])
        search_query = f"recipes with {ingredients_str}"
    else:
        search_query = state["query"]

    logger.debug(f"Search query: {search_query}")

    # Perform search using the tool
    search_results = tavily_search_tool.search_recipes(search_query)

    logger.debug(f"Found {len(search_results)} results")

    return {"search_results": search_results}


def cookware_verification_node(state: CookingGraphState) -> dict:
    """
    This node verifies if the user has the required cookware.

    INPUT: Reads state["required_cookware"]
    OUTPUT: Returns dict with can_cook and missing_cookware
    """
    logger.info("COOKWARE VERIFICATION NODE: Checking cookware requirements")

    required_cookware = state.get("required_cookware", [])

    if not required_cookware:
        # No cookware requirements specified
        logger.debug("No cookware requirements specified")
        return {"can_cook": True, "missing_cookware": []}

    # Convert to lowercase for case-insensitive comparison
    available_lower = [item.lower() for item in AVAILABLE_COOKWARE]

    # Check which required items are missing
    missing = []
    for item in required_cookware:
        if item.lower() not in available_lower:
            missing.append(item)

    can_cook = len(missing) == 0

    logger.debug(f"Cookware check - Required: {required_cookware}, Missing: {missing}, Can cook: {can_cook}")

    return {"can_cook": can_cook, "missing_cookware": missing}
