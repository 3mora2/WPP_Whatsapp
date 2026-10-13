"""Legacy data-URI downloads over bounded media preparation."""

from __future__ import annotations

import asyncio
import base64
import logging
import re
from typing import List, Optional, Union

import aiohttp

from WPP_Whatsapp.core.media import DEFAULT_MAX_BYTES, MediaTooLargeError, prepare_media

logger = logging.getLogger(__name__)


async def downloadFileToBase64(
    _path: str,
    _mines: Optional[List[Union[str, re.Pattern]]] = None,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> Union[str, bool]:
    """Keep the data-URI/False contract with a hard byte limit and safe logging.

    Legacy consumers still buffer the bounded base64 result. New code should
    use messages.send_media for chunked browser transfer instead.
    """
    if _mines is None:
        _mines = []
    if not isinstance(_mines, list):
        return False
    if not isinstance(_path, str) or not re.match(r"^https?://", _path, re.IGNORECASE):
        return False
    try:
        async with prepare_media(_path, max_bytes=max_bytes, timeout=60) as media:
            mime = media.mimetype.split(";", 1)[0].strip().lower()
            if _mines and not any(
                rule.fullmatch(mime) if isinstance(rule, re.Pattern) else rule == mime
                for rule in _mines
            ):
                return False
            encoded = base64.b64encode(media.path.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{encoded}"
    except (aiohttp.ClientError, asyncio.TimeoutError, MediaTooLargeError, OSError):
        # URLs and network exception strings can contain private credentials.
        logger.warning("Media download failed or exceeded its configured byte limit")
        return False
