"""
Batch Operations for WPPConnect

Provides bulk/batch operations for efficient mass messaging and operations.
"""

from __future__ import annotations

import asyncio
from typing import List, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum

from WPP_Whatsapp.api.model import SendTextOptions


class BatchStatus(Enum):
    """Status of batch operation"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class BatchResult:
    """Result of a batch operation"""
    total: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    status: BatchStatus
    duration: float


class BatchOperations:
    """
    Batch operations for efficient bulk operations

    Example:
        batch = BatchOperations(client)

        # Send bulk messages
        messages = [
            {"to": "123@c.us", "content": "Hello 1"},
            {"to": "456@c.us", "content": "Hello 2"},
        ]
        result = await batch.send_bulk_text(messages)

        print(f"Sent {result.successful}/{result.total} messages")
    """

    def __init__(self, client, rate_limiter=None):
        """
        Initialize batch operations

        @param client: Whatsapp client instance
        @param rate_limiter: Optional rate limiter instance
        """
        self.client = client
        self.rate_limiter = rate_limiter

    async def send_bulk_text(
        self,
        messages: List[Dict[str, Any]],
        options: Optional[SendTextOptions] = None,
        concurrency: int = 1,
        on_progress: Optional[Callable[[int, int], None]] = None
    ) -> BatchResult:
        """
        Send bulk text messages

        @param messages: List of message dicts with 'to' and 'content' keys
        @param options: Optional message options
        @param concurrency: Number of concurrent sends (1 = sequential)
        @param on_progress: Optional callback(current, total) for progress updates
        @return: BatchResult with success/failure counts
        """
        import time
        start_time = time.time()

        results = []
        errors = []
        successful = 0
        failed = 0

        async def send_message(msg_data: Dict[str, Any], index: int):
            nonlocal successful, failed
            try:
                if self.rate_limiter:
                    async with self.rate_limiter:
                        result = await self.client.sendText(
                            msg_data["to"],
                            msg_data["content"],
                            options
                        )
                else:
                    result = await self.client.sendText(
                        msg_data["to"],
                        msg_data["content"],
                        options
                    )

                results.append({
                    "index": index,
                    "to": msg_data["to"],
                    "success": True,
                    "result": result
                })
                successful += 1

                if on_progress:
                    on_progress(successful + failed, len(messages))

            except Exception as e:
                errors.append({
                    "index": index,
                    "to": msg_data["to"],
                    "success": False,
                    "error": str(e)
                })
                failed += 1

                if on_progress:
                    on_progress(successful + failed, len(messages))

        # Run with concurrency control
        if concurrency > 1:
            semaphore = asyncio.Semaphore(concurrency)

            async def limited_send(msg_data, index):
                async with semaphore:
                    await send_message(msg_data, index)

            tasks = [limited_send(msg, i) for i, msg in enumerate(messages)]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Sequential processing
            for i, msg in enumerate(messages):
                await send_message(msg, i)

        # Determine status
        if failed == 0:
            status = BatchStatus.COMPLETED
        elif successful == 0:
            status = BatchStatus.FAILED
        else:
            status = BatchStatus.PARTIAL

        return BatchResult(
            total=len(messages),
            successful=successful,
            failed=failed,
            results=results,
            errors=errors,
            status=status,
            duration=time.time() - start_time
        )

    async def send_bulk_to_group(
        self,
        group_id: str,
        content: str,
        member_ids: Optional[List[str]] = None,
        options: Optional[SendTextOptions] = None,
        concurrency: int = 1
    ) -> BatchResult:
        """
        Send message to all/specific members of a group

        @param group_id: Group ID
        @param content: Message content
        @param member_ids: Optional list of specific member IDs (None = all members)
        @param options: Optional message options
        @param concurrency: Number of concurrent sends
        @return: BatchResult
        """
        # Get group members
        if not member_ids:
            members = await self.client.getGroupMembers(group_id)
            member_ids = [member.get("id", {}).get("_serialized") for member in members]

        # Prepare messages
        messages = [
            {"to": member_id, "content": content}
            for member_id in member_ids
        ]

        return await self.send_bulk_text(messages, options, concurrency)

    async def forward_to_many(
        self,
        message_id: str,
        chat_ids: List[str],
        concurrency: int = 1
    ) -> BatchResult:
        """
        Forward a message to multiple chats

        @param message_id: Message ID to forward
        @param chat_ids: List of chat IDs to forward to
        @param concurrency: Number of concurrent forwards
        @return: BatchResult
        """
        import time
        start_time = time.time()

        results = []
        errors = []
        successful = 0
        failed = 0

        async def forward_message(chat_id: str, index: int):
            nonlocal successful, failed
            try:
                if self.rate_limiter:
                    async with self.rate_limiter:
                        result = await self.client.forwardMessages(chat_id, message_id)
                else:
                    result = await self.client.forwardMessages(chat_id, message_id)

                results.append({
                    "index": index,
                    "to": chat_id,
                    "success": True,
                    "result": result
                })
                successful += 1
            except Exception as e:
                errors.append({
                    "index": index,
                    "to": chat_id,
                    "success": False,
                    "error": str(e)
                })
                failed += 1

        if concurrency > 1:
            semaphore = asyncio.Semaphore(concurrency)

            async def limited_forward(chat_id, index):
                async with semaphore:
                    await forward_message(chat_id, index)

            tasks = [limited_forward(chat_id, i) for i, chat_id in enumerate(chat_ids)]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            for i, chat_id in enumerate(chat_ids):
                await forward_message(chat_id, i)

        # Determine status
        if failed == 0:
            status = BatchStatus.COMPLETED
        elif successful == 0:
            status = BatchStatus.FAILED
        else:
            status = BatchStatus.PARTIAL

        return BatchResult(
            total=len(chat_ids),
            successful=successful,
            failed=failed,
            results=results,
            errors=errors,
            status=status,
            duration=time.time() - start_time
        )

    async def delete_many_messages(
        self,
        chat_id: str,
        message_ids: List[str],
        only_local: bool = False,
        delete_media: bool = True,
        concurrency: int = 3
    ) -> BatchResult:
        """
        Delete multiple messages from a chat

        @param chat_id: Chat ID
        @param message_ids: List of message IDs to delete
        @param only_local: Only delete locally
        @param delete_media: Delete media from device
        @param concurrency: Number of concurrent deletes
        @return: BatchResult
        """
        import time
        start_time = time.time()

        results = []
        errors = []
        successful = 0
        failed = 0

        async def delete_message(msg_id: str, index: int):
            nonlocal successful, failed
            try:
                result = await self.client.deleteMessage(
                    chat_id,
                    msg_id,
                    only_local,
                    delete_media
                )

                results.append({
                    "index": index,
                    "message_id": msg_id,
                    "success": True,
                    "result": result
                })
                successful += 1
            except Exception as e:
                errors.append({
                    "index": index,
                    "message_id": msg_id,
                    "success": False,
                    "error": str(e)
                })
                failed += 1

        if concurrency > 1:
            semaphore = asyncio.Semaphore(concurrency)

            async def limited_delete(msg_id, index):
                async with semaphore:
                    await delete_message(msg_id, index)

            tasks = [limited_delete(msg_id, i) for i, msg_id in enumerate(message_ids)]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            for i, msg_id in enumerate(message_ids):
                await delete_message(msg_id, i)

        # Determine status
        if failed == 0:
            status = BatchStatus.COMPLETED
        elif successful == 0:
            status = BatchStatus.FAILED
        else:
            status = BatchStatus.PARTIAL

        return BatchResult(
            total=len(message_ids),
            successful=successful,
            failed=failed,
            results=results,
            errors=errors,
            status=status,
            duration=time.time() - start_time
        )
