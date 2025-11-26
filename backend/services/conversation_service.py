import logging
import uuid
from datetime import datetime

from langchain_openai import ChatOpenAI

from database.connection import get_db
from database.models import Conversation, Message

logger = logging.getLogger(__name__)


def generate_conversation_title(first_message: str) -> str:
    """Generate a concise title from the first user message using LLM."""
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5, max_tokens=20)
        prompt = f"""Generate a concise, descriptive 2-5 word title for this cooking question.
Focus on the main topic (dish, ingredient, or technique).
Be specific and clear. Do not use quotes or punctuation.

Question: {first_message}

Title:"""
        response = llm.invoke(prompt)
        title = response.content.strip("\"'.,!?").strip()
        return title if title else "New Conversation"
    except Exception as e:
        logger.error(f"Error generating title: {e}")
        return "New Conversation"


def create_conversation(thread_id: str, first_message: str | None = None) -> Conversation:
    """Create a new conversation with optional title generation."""
    with get_db() as db:
        title = generate_conversation_title(first_message) if first_message else "New Conversation"
        conv = Conversation(id=str(uuid.uuid4()), thread_id=thread_id, title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        logger.info(f"Created conversation: {conv.thread_id} with title '{title}'")
        return conv


def get_conversation_by_thread(thread_id: str) -> Conversation | None:
    """Fetch a conversation by thread_id."""
    with get_db() as db:
        return db.query(Conversation).filter_by(thread_id=thread_id).first()


def save_message(thread_id: str, role: str, content: str, metadata: dict = None) -> Message:
    """Save a message to the database and update conversation metadata."""
    with get_db() as db:
        # Get or create conversation
        conv = db.query(Conversation).filter_by(thread_id=thread_id).first()
        if not conv:
            # Create conversation without title generation (will be done on first user message)
            first_user_message = content if role == "user" else None
            conv = Conversation(
                id=str(uuid.uuid4()),
                thread_id=thread_id,
                title=generate_conversation_title(first_user_message)
                if first_user_message
                else "New Conversation",
            )
            db.add(conv)
            db.flush()  # Get the ID without committing

        # Create message
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            thread_id=thread_id,
            role=role,
            content=content,
            message_metadata=metadata or {},
        )
        db.add(message)

        # Update conversation metadata
        conv.message_count += 1
        conv.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(message)
        logger.debug(f"Saved {role} message to conversation {thread_id}")
        return message


def list_conversations(skip: int = 0, limit: int = 50) -> list[Conversation]:
    """List all conversations, ordered by most recent first."""
    with get_db() as db:
        return (
            db.query(Conversation)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


def get_conversation_messages(thread_id: str) -> list[Message]:
    """Fetch all messages for a conversation."""
    with get_db() as db:
        return (
            db.query(Message).filter_by(thread_id=thread_id).order_by(Message.timestamp.asc()).all()
        )


def delete_conversation(thread_id: str) -> bool:
    """Delete a conversation and all its messages."""
    with get_db() as db:
        conv = db.query(Conversation).filter_by(thread_id=thread_id).first()
        if conv:
            db.delete(conv)  # Cascade will delete messages
            db.commit()
            logger.info(f"Deleted conversation: {thread_id}")
            return True
        return False


def update_conversation_title(thread_id: str, title: str) -> Conversation | None:
    """Update a conversation's title."""
    with get_db() as db:
        conv = db.query(Conversation).filter_by(thread_id=thread_id).first()
        if conv:
            conv.title = title
            conv.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(conv)
            logger.info(f"Updated conversation {thread_id} title to '{title}'")
            return conv
        return None
