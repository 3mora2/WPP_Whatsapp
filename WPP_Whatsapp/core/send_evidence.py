"""Pre-dispatch identity and conservative reconciliation for supported sends."""

from .delivery_models import ExpectedMessage
from .models import identifier
from .work import controller


async def reserve_message(context, chat_id, kind, message_id=None, *, admitted=False):
    bridge = context.bridge

    async def allocate():
        context.lifecycle.require_ready()
        return await bridge.call("Messages.reserve", {"chatId": chat_id, "messageId": message_id})

    if admitted:
        result = await allocate()
    else:
        async with controller(context).slot():
            result = await allocate()
    key, canonical = result["id"], result["chatId"]
    if (
        not isinstance(key, str)
        or not isinstance(canonical, str)
        or not key.startswith("true_" + canonical + "_")
    ):
        raise ValueError("Runtime returned an invalid outgoing message key")
    return ExpectedMessage(key, canonical, kind)


def matches_expected(message, expected):
    try:
        key = identifier(message.get("id"))
        return (
            key == expected.message_id
            and key.startswith("true_" + expected.chat_id + "_")
            and message.get("fromMe") is True
            and (
                message.get("type") == expected.type
                or (expected.type == "audio" and message.get("type") == "ptt")
            )
        )
    except (ValueError, AttributeError):
        return False
