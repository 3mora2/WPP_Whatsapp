"""Bounded media preparation and chunked browser transfer; no whole-file base64 in Python."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import inspect
import mimetypes
import tempfile
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Optional, Union

import aiohttp

from .bridge import JavascriptBridge
from .errors import BridgeError

CHUNK_BYTES = 256 * 1024
DEFAULT_MAX_BYTES = 64 * 1024 * 1024
Progress = Callable[[int, Optional[int]], Union[None, Awaitable[None]]]


class MediaTooLargeError(ValueError):
    def __init__(self):
        super().__init__("Media exceeds the configured byte limit")


async def report(callback: Optional[Progress], completed: int, total: Optional[int]) -> None:
    if callback is not None:
        result = callback(completed, total)
        if inspect.isawaitable(result):
            await result


@dataclass(frozen=True)
class PreparedMedia:
    path: Path
    size: int
    mimetype: str
    filename: str


@asynccontextmanager
async def prepare_media(
    source: Union[str, Path],
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    progress: Optional[Progress] = None,
    timeout: float = 120,
):
    """Copy a local file or HTTP response to a private temporary file, with hard limits.

    Temporary files are removed on success, error and cancellation. This core API
    accepts URLs; MCP exposes only files under an administrator-configured root.
    """
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("max_bytes must be a positive integer")
    source = str(source)
    with tempfile.TemporaryDirectory(prefix="wpp-media-") as directory:
        target = Path(directory) / "payload"
        size = 0
        mime = "application/octet-stream"
        filename = "attachment"

        async def write_chunk(output, chunk, total):
            nonlocal size
            size += len(chunk)
            if size > max_bytes:
                raise MediaTooLargeError()
            output.write(chunk)
            await report(progress, size, total)

        with target.open("wb") as output:
            if source.lower().startswith(("https://", "http://")):
                request_timeout = aiohttp.ClientTimeout(total=timeout, connect=10)
                async with aiohttp.ClientSession(timeout=request_timeout) as session:
                    async with session.get(source) as response:
                        response.raise_for_status()
                        total = response.content_length
                        if total is not None and total > max_bytes:
                            raise MediaTooLargeError()
                        mime = response.content_type or mime
                        async for chunk in response.content.iter_chunked(CHUNK_BYTES):
                            await write_chunk(output, chunk, total)
            else:
                path = Path(source)
                filename = path.name
                mime = mimetypes.guess_type(filename)[0] or mime
                with path.open("rb") as incoming:
                    total = path.stat().st_size
                    if total > max_bytes:
                        raise MediaTooLargeError()
                    while True:
                        chunk = incoming.read(CHUNK_BYTES)
                        if not chunk:
                            break
                        await write_chunk(output, chunk, total)
                        await asyncio.sleep(0)  # Cancellation even without a progress callback.
        yield PreparedMedia(target, size, mime, filename)


async def send_prepared(
    context,
    chat_id: str,
    media: PreparedMedia,
    *,
    kind: str,
    caption: str = "",
    quoted_message_id: Optional[str] = None,
    progress: Optional[Progress] = None,
) -> dict:
    """Transfer chunks to a File accepted by WA-JS; browser still buffers the file."""
    if kind not in {"document", "image", "video", "audio"}:
        raise ValueError("Unsupported media kind")
    bridge = _bridge(context)
    key = uuid.uuid4().hex
    dispatched = False
    try:
        await bridge.call("Media.begin", key)
        completed = 0
        with media.path.open("rb") as incoming:
            while True:
                chunk = incoming.read(CHUNK_BYTES)
                if not chunk:
                    break
                await bridge.call(
                    "Media.append", {"key": key, "data": base64.b64encode(chunk).decode("ascii")}
                )
                completed += len(chunk)
                await report(progress, completed, media.size)
        dispatched = True
        return await bridge.call(
            "Media.send",
            {
                "key": key,
                "chatId": chat_id,
                "filename": media.filename,
                "mimetype": media.mimetype,
                "type": kind,
                "caption": caption,
                "quotedMsg": quoted_message_id,
            },
        )
    except BridgeError:
        raise BridgeError("messages.send_media", dispatched=dispatched) from None
    finally:
        # Preserve the original failure; a closed browser already released its buffers.
        try:
            await bridge.call("Media.release", key)
        except Exception:
            pass


async def download_to(
    context,
    message_id: str,
    destination: Union[str, Path],
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    progress: Optional[Progress] = None,
) -> dict:
    """Save a WA-JS Blob in chunks, refusing to overwrite an existing file."""
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("max_bytes must be a positive integer")
    path = Path(destination)
    bridge = _bridge(context)
    key = uuid.uuid4().hex
    created = False
    try:
        info = await bridge.call(
            "Media.download", {"key": key, "id": message_id, "maxBytes": max_bytes}
        )
        size = info["size"]
        if type(size) is not int or not 0 <= size <= max_bytes:
            raise MediaTooLargeError()
        digest = hashlib.sha256()
        with path.open("xb") as output:
            created = True
            for offset in range(0, size, CHUNK_BYTES):
                encoded = await bridge.call(
                    "Media.read", {"key": key, "offset": offset, "size": CHUNK_BYTES}
                )
                chunk = base64.b64decode(encoded, validate=True)
                if len(chunk) != min(CHUNK_BYTES, size - offset):
                    raise ValueError("Incomplete media transfer")
                output.write(chunk)
                digest.update(chunk)
                await report(progress, offset + len(chunk), size)
        return {"size": size, "sha256": digest.hexdigest(), "mimetype": info["mimetype"]}
    except BaseException:
        if created:
            path.unlink(missing_ok=True)
        raise
    finally:
        try:
            await bridge.call("Media.release", key)
        except Exception:
            pass


def _bridge(context):
    bridge = getattr(context, "bridge", None)
    if bridge is None:
        bridge = context.bridge = JavascriptBridge(context.ThreadsafeBrowser, context.page)
    return bridge
