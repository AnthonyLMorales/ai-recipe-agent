import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from graphs.cooking_graph import cooking_graph
from schemas import QueryInput, QueryResponse
from services import conversation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cooking", tags=["cooking"])

# Thinking step messages for user-friendly display
THINKING_MESSAGES = {
    "classifier": "Analyzing your question...",
    "decide_search": "Determining information needs...",
    "search": "Searching for recipes...",
    "cookware_verification": "Checking cookware requirements...",
    "response": "Generating response...",
    "refusal": "Processing query...",
}


@router.post("", response_model=QueryResponse)
async def cooking_endpoint(payload: QueryInput):
    """
    Main endpoint for cooking queries with conversation memory.
    Runs the query through the LangGraph workflow.
    """
    try:
        logger.info(f"Received query: {payload.query} (thread: {payload.thread_id})")

        # Save user message to database
        conversation_service.save_message(
            thread_id=payload.thread_id, role="user", content=payload.query
        )

        # Initialize state for this turn
        initial_state = {
            "query": payload.query,
            "search_results": [],  # Initialize as empty list
            # messages will be loaded from checkpoint if thread exists
        }

        # Thread configuration for checkpointer
        config = {"configurable": {"thread_id": payload.thread_id}}

        # Run the graph with thread context
        # If thread_id exists: loads previous state from database
        # If new thread_id: starts fresh
        result = cooking_graph.invoke(initial_state, config)

        # Save assistant message to database
        conversation_service.save_message(
            thread_id=payload.thread_id,
            role="assistant",
            content=result.get("final_response", "No response generated."),
            metadata={
                "query_type": result.get("query_type"),
                "is_relevant": result.get("is_relevant"),
                "dish": result.get("dish"),
            },
        )

        logger.info(f"Graph completed. Thread: {payload.thread_id}")

        return QueryResponse(
            response=result.get("final_response", "No response generated."),
            metadata={
                "query_type": result.get("query_type"),
                "is_relevant": result.get("is_relevant"),
                "dish": result.get("dish"),
            },
            thread_id=payload.thread_id,
        )

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stream")
async def cooking_stream_endpoint(payload: QueryInput):
    """
    Streaming endpoint for cooking queries with real-time progress updates.
    Uses Server-Sent Events (SSE) to stream node execution progress.
    """

    async def event_generator():
        """Generate SSE events as graph executes."""
        try:
            logger.info(f"Starting stream for query: {payload.query}")

            # Save user message
            conversation_service.save_message(
                thread_id=payload.thread_id, role="user", content=payload.query
            )

            # Initialize state
            initial_state = {
                "query": payload.query,
                "search_results": [],
            }

            # Thread configuration
            config = {"configurable": {"thread_id": payload.thread_id}}

            # Track final result
            final_result = None

            # Stream graph execution
            async for event in cooking_graph.astream(initial_state, config):
                # event is a dict: {node_name: state_update}
                for node_name, state_update in event.items():
                    logger.info(f"Streaming node: {node_name}")

                    # Send thinking step event
                    thinking_event = {
                        "type": "thinking",
                        "node": node_name,
                        "message": THINKING_MESSAGES.get(node_name, f"Processing {node_name}..."),
                    }
                    yield f"data: {json.dumps(thinking_event)}\n\n"

                    # Store final result
                    if "final_response" in state_update:
                        final_result = state_update

            # Get final state (if not captured in events)
            if final_result is None:
                final_result = cooking_graph.get_state(config).values

            # Save assistant message
            conversation_service.save_message(
                thread_id=payload.thread_id,
                role="assistant",
                content=final_result.get("final_response", "No response generated."),
                metadata={
                    "query_type": final_result.get("query_type"),
                    "is_relevant": final_result.get("is_relevant"),
                    "dish": final_result.get("dish"),
                },
            )

            # Send completion event
            complete_event = {
                "type": "complete",
                "response": final_result.get("final_response", "No response generated."),
                "metadata": {
                    "query_type": final_result.get("query_type"),
                    "is_relevant": final_result.get("is_relevant"),
                    "dish": final_result.get("dish"),
                },
                "thread_id": payload.thread_id,
            }
            yield f"data: {json.dumps(complete_event)}\n\n"

            logger.info(f"Stream completed for thread: {payload.thread_id}")

        except Exception as e:
            logger.error(f"Stream error: {str(e)}", exc_info=True)
            error_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
