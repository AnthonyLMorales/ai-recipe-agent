import logging
import uuid

from fastapi import APIRouter, HTTPException

from schemas.conversation import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationSchema,
    ConversationWithLastMessage,
    CreateConversationRequest,
    MessageSchema,
    UpdateConversationRequest,
)
from services import conversation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=ConversationListResponse)
async def list_conversations(skip: int = 0, limit: int = 50):
    """List all conversations, ordered by most recent first."""
    try:
        conversations = conversation_service.list_conversations(skip, limit)

        # Convert to response format with last message
        conversations_with_last = []
        for conv in conversations:
            # Get last message for this conversation
            messages = conversation_service.get_conversation_messages(conv.thread_id)
            last_message = messages[-1] if messages else None

            conv_dict = {
                "id": conv.id,
                "thread_id": conv.thread_id,
                "title": conv.title,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "message_count": conv.message_count,
                "last_message": MessageSchema.model_validate(last_message)
                if last_message
                else None,
            }
            conversations_with_last.append(ConversationWithLastMessage(**conv_dict))

        return ConversationListResponse(
            conversations=conversations_with_last, total=len(conversations)
        )
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{thread_id}", response_model=ConversationDetailResponse)
async def get_conversation(thread_id: str):
    """Get a specific conversation with all messages."""
    try:
        conversation = conversation_service.get_conversation_by_thread(thread_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = conversation_service.get_conversation_messages(thread_id)

        return ConversationDetailResponse(
            conversation=ConversationSchema.model_validate(conversation),
            messages=[MessageSchema.model_validate(m) for m in messages],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("", response_model=ConversationSchema)
async def create_conversation(request: CreateConversationRequest = None):
    """Create a new conversation."""
    try:
        thread_id = str(uuid.uuid4())
        title = request.title if request and request.title else None
        conversation = conversation_service.create_conversation(thread_id, title)
        return ConversationSchema.model_validate(conversation)
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{thread_id}", response_model=ConversationSchema)
async def update_conversation(thread_id: str, request: UpdateConversationRequest):
    """Update conversation title."""
    try:
        conversation = conversation_service.update_conversation_title(thread_id, request.title)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return ConversationSchema.model_validate(conversation)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{thread_id}")
async def delete_conversation(thread_id: str):
    """Delete a conversation and all its messages."""
    try:
        success = conversation_service.delete_conversation(thread_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"status": "deleted", "thread_id": thread_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
