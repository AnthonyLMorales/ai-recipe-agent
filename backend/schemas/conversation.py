from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageSchema(BaseModel):
    """Schema for a message in a conversation."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    conversation_id: str
    thread_id: str
    role: str
    content: str
    timestamp: datetime
    message_metadata: dict | None = Field(
        None, serialization_alias="metadata"
    )  # Expose as 'metadata' in API, but read as 'message_metadata' from models


class ConversationSchema(BaseModel):
    """Schema for a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    thread_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationWithLastMessage(ConversationSchema):
    """Conversation schema with the last message included."""

    last_message: MessageSchema | None = None


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""

    conversations: list[ConversationWithLastMessage]
    total: int


class ConversationDetailResponse(BaseModel):
    """Response for getting a single conversation with all messages."""

    conversation: ConversationSchema
    messages: list[MessageSchema]


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""

    title: str | None = None


class UpdateConversationRequest(BaseModel):
    """Request to update conversation metadata."""

    title: str
