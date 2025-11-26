import asyncio
import base64
import builtins
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)

from database.connection import get_db
from database.models import Checkpoint as CheckpointModel

logger = logging.getLogger(__name__)


class SQLiteCheckpointSaver(BaseCheckpointSaver):
    """SQLite-backed checkpoint saver for LangGraph."""

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Fetch a checkpoint tuple using the given configuration."""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None

        try:
            with get_db() as db:
                record = (
                    db.query(CheckpointModel)
                    .filter_by(thread_id=thread_id)
                    .order_by(CheckpointModel.created_at.desc())
                    .first()
                )

                if record:
                    checkpoint_data = record.checkpoint_data
                    # Deserialize checkpoint
                    type_str = checkpoint_data["checkpoint"]["type"]
                    data = checkpoint_data["checkpoint"]["data"]

                    # Decode base64 string back to bytes if needed
                    if isinstance(data, str):
                        data = base64.b64decode(data)

                    checkpoint = self.serde.loads_typed((type_str, data))
                    metadata = checkpoint_data.get("metadata", {})

                    return CheckpointTuple(
                        config=config,
                        checkpoint=checkpoint,
                        metadata=metadata,
                        parent_config=None,
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting checkpoint for thread {thread_id}: {e}")
            return None

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints that match the given criteria."""
        thread_id = config.get("configurable", {}).get("thread_id") if config else None

        try:
            with get_db() as db:
                query = db.query(CheckpointModel)

                if thread_id:
                    query = query.filter_by(thread_id=thread_id)

                query = query.order_by(CheckpointModel.created_at.desc())

                if limit:
                    query = query.limit(limit)

                records = query.all()

                for record in records:
                    checkpoint_data = record.checkpoint_data
                    # Deserialize checkpoint
                    type_str = checkpoint_data["checkpoint"]["type"]
                    data = checkpoint_data["checkpoint"]["data"]

                    # Decode base64 string back to bytes if needed
                    if isinstance(data, str):
                        data = base64.b64decode(data)

                    checkpoint = self.serde.loads_typed((type_str, data))
                    metadata = checkpoint_data.get("metadata", {})

                    yield CheckpointTuple(
                        config={"configurable": {"thread_id": record.thread_id}},
                        checkpoint=checkpoint,
                        metadata=metadata,
                        parent_config=None,
                    )
        except Exception as e:
            logger.error(f"Error listing checkpoints: {e}")
            return

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,
    ) -> RunnableConfig:
        """Store a checkpoint with its configuration and metadata."""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            raise ValueError("thread_id required in config['configurable']")

        try:
            # Serialize checkpoint
            type_str, serialized_data = self.serde.dumps_typed(checkpoint)

            # Convert bytes to base64 string for JSON storage
            if isinstance(serialized_data, bytes):
                serialized_data = base64.b64encode(serialized_data).decode("utf-8")

            checkpoint_data = {
                "checkpoint": {"type": type_str, "data": serialized_data},
                "metadata": dict(metadata) if metadata else {},
            }

            with get_db() as db:
                checkpoint_record = CheckpointModel(
                    thread_id=thread_id, checkpoint_data=checkpoint_data
                )
                db.add(checkpoint_record)
                db.commit()

            logger.debug(f"Saved checkpoint for thread {thread_id}")
            return config
        except Exception as e:
            logger.error(f"Error saving checkpoint for thread {thread_id}: {e}")
            raise

    def put_writes(
        self,
        config: RunnableConfig,
        writes: builtins.list[tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Store intermediate writes for a task.

        This is called during graph execution to save intermediate state.
        For a simple implementation, we can store these as part of the checkpoint
        or just pass - they'll be included in the next checkpoint save.
        """
        # For now, we don't need to persist intermediate writes separately
        # They will be included in the checkpoint when put() is called
        pass

    # Async versions of the methods for async graph execution
    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Async version of get_tuple."""
        return await asyncio.to_thread(self.get_tuple, config)

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """Async version of list."""
        # Run the sync list in a thread and yield results
        for item in await asyncio.to_thread(
            lambda: list(self.list(config, filter=filter, before=before, limit=limit))
        ):
            yield item

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,
    ) -> RunnableConfig:
        """Async version of put."""
        return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: builtins.list[tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Async version of put_writes."""
        await asyncio.to_thread(self.put_writes, config, writes, task_id)
