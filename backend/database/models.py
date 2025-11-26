import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Conversation(Base):
    """Represents a conversation thread with multiple messages."""

    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    message_count = Column(Integer, default=0)

    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Represents a single message in a conversation."""

    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), index=True)
    thread_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # 'user' or 'assistant' or 'error'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_metadata = Column(
        JSON, nullable=True
    )  # Renamed from 'metadata' to avoid SQLAlchemy conflict

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")


class Checkpoint(Base):
    """Stores LangGraph checkpoint data for conversation continuity."""

    __tablename__ = "checkpoints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String, nullable=False, index=True)
    checkpoint_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
