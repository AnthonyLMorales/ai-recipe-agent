import logging

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph

from checkpointer.sqlite_checkpointer import SQLiteCheckpointSaver

from .nodes import classifier_node, cookware_verification_node, decide_search_node, search_node
from .state import CookingGraphState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create SQLite checkpointer for persistent conversation memory
checkpointer = SQLiteCheckpointSaver()


def build_cooking_graph():
    """
    Builds and returns the cooking assistant graph.
    """

    workflow = StateGraph(CookingGraphState)

    # Add all nodes
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("decide_search", decide_search_node)
    workflow.add_node("search", search_node)
    workflow.add_node("cookware_verification", cookware_verification_node)

    # Refusal node
    def refusal_node(state: CookingGraphState) -> dict:
        logger.info("REFUSAL NODE: Query not cooking-related")
        return {
            "final_response": "I'm a cooking assistant and can only help with cooking and recipe-related questions. Please ask me something about cooking!"
        }

    workflow.add_node("refusal", refusal_node)

    # Enhanced response node
    def response_node(state: CookingGraphState) -> dict:
        """Generate final response using LLM."""
        logger.info("RESPONSE NODE: Generating final response")

        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5, max_tokens=300)

        # Build conversation context from message history
        conversation_context = ""
        if state.get("messages"):
            recent_messages = state["messages"][-6:]  # Last 3 exchanges
            conversation_context = "\n\nConversation History:\n"
            for msg in recent_messages:
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                conversation_context += f"{role}: {msg.content}\n"

        # Build context from search results
        search_context = ""
        if state.get("search_results"):
            search_context = "\n\nWeb Search Results:\n"
            for result in state["search_results"]:
                search_context += f"{result.get('results', '')}\n"

        # Build cookware context
        cookware_context = ""
        if state.get("required_cookware"):
            cookware_context = f"\n\nRequired Cookware: {', '.join(state['required_cookware'])}"

            can_cook = state.get("can_cook")
            missing_cookware = state.get("missing_cookware", [])

            if can_cook is False and missing_cookware:
                cookware_context += f"\nIMPORTANT: You are missing the following cookware: {', '.join(missing_cookware)}"
                cookware_context += "\nYou may not be able to make this recipe without these items."
            elif can_cook:
                cookware_context += "\nYou have all the required cookware to make this recipe!"

        prompt = ChatPromptTemplate.from_template("""
            You are a helpful cooking assistant. Keep your response concise and to the point.

            {conversation_context}

            Current User Query: {query}
            Query Type: {query_type}
            Dish: {dish}
            Ingredients: {ingredients}

            {search_context}
            {cookware_context}

            Provide a brief, helpful response. Reference previous conversation when relevant.
            For example, if the user asked about a recipe and now asks a follow-up question,
            acknowledge the connection ("For the carbonara we discussed...").

            If it's a recipe, give the key steps only.
            If the user is missing cookware, acknowledge this and suggest alternatives if possible.
            Keep it under 250 words.
        """)

        chain = prompt | llm

        response = chain.invoke(
            {
                "conversation_context": conversation_context,
                "query": state["query"],
                "query_type": state.get("query_type", "unknown"),
                "dish": state.get("dish", "not specified"),
                "ingredients": state.get("ingredients", []),
                "search_context": search_context,
                "cookware_context": cookware_context,
            }
        )

        # Add assistant response to message history
        messages_update = [AIMessage(content=response.content)]

        return {"final_response": response.content, "messages": messages_update}

    workflow.add_node("response", response_node)

    # Set entry point
    workflow.set_entry_point("classifier")

    # Route after classification
    def route_after_classification(state: CookingGraphState) -> str:
        logger.info(f"ROUTING AFTER CLASSIFICATION: is_relevant={state.get('is_relevant')}")

        if not state.get("is_relevant"):
            return "refusal"
        else:
            return "decide_search"

    workflow.add_conditional_edges(
        "classifier",
        route_after_classification,
        {
            "refusal": "refusal",
            "decide_search": "decide_search",
        },
    )

    # Route after search decision
    def route_after_search_decision(state: CookingGraphState) -> str:
        needs_search = state.get("needs_search", False)
        logger.info(f"ROUTING AFTER SEARCH DECISION: needs_search={needs_search}")

        if needs_search:
            return "search"
        else:
            return "response"

    workflow.add_conditional_edges(
        "decide_search",
        route_after_search_decision,
        {
            "search": "search",
            "response": "cookware_verification",
        },
    )

    # After search, go to cookware verification
    workflow.add_edge("search", "cookware_verification")

    # After cookware verification, go to response
    workflow.add_edge("cookware_verification", "response")

    # End edges
    workflow.add_edge("refusal", END)
    workflow.add_edge("response", END)

    # Compile with checkpointer for conversation memory
    app = workflow.compile(checkpointer=checkpointer)

    return app


cooking_graph = build_cooking_graph()
