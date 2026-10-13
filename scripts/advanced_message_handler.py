"""
Advanced Message Handler Example

This example demonstrates:
- Command routing system
- Message middleware
- Context management
- Error handling
- Logging
"""

import asyncio
import logging
from typing import Any, Callable, Dict

from WPP_Whatsapp import Create

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MessageRouter:
    """Route messages to appropriate handlers based on commands"""

    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.middleware: list = []

    def register_command(self, command: str):
        """Decorator to register a command handler"""

        def decorator(func: Callable):
            self.handlers[command.lower()] = func
            logger.info(f"Registered command: {command}")
            return func

        return decorator

    def use(self, middleware_func: Callable):
        """Add middleware to the pipeline"""
        self.middleware.append(middleware_func)

    async def handle(self, client, message: Dict[str, Any]):
        """Process incoming message"""
        # Run middleware
        for mw in self.middleware:
            should_continue = await mw(client, message)
            if not should_continue:
                return

        # Get message text
        text = (message.get("body") or "").strip()
        if not text:
            return

        # Check if it's a command
        if text.startswith("/"):
            command = text.split()[0].lower()
            handler = self.handlers.get(command)

            if handler:
                try:
                    await handler(client, message)
                except Exception as e:
                    logger.error(f"Error in command {command}: {e}")
                    await client.sendText_(
                        message.get("from"), f"❌ Error executing command: {str(e)}"
                    )
            else:
                await client.sendText_(
                    message.get("from"),
                    f"❌ Unknown command: {command}\nUse /help for available commands",
                )


# Create router instance
router = MessageRouter()


# Middleware: Log all messages
async def log_messages(client, message):
    logger.info("Incoming message type: %s", message.get("type"))
    return True  # Continue processing


# Middleware: Ignore group messages
async def ignore_groups(client, message):
    if message.get("isGroupMsg"):
        return False  # Stop processing
    return True


# Middleware: Block specific users
BLOCKED_USERS = ["blocked_number@c.us"]


async def check_blocked(client, message):
    if message.get("from") in BLOCKED_USERS:
        return False
    return True


# Register middleware
router.use(log_messages)
router.use(ignore_groups)
router.use(check_blocked)


# Command Handlers
@router.register_command("/hello")
async def cmd_hello(client, message):
    """Greet the user"""
    await client.sendText_(message.get("from"), "👋 Hello! How can I help you?")


@router.register_command("/help")
async def cmd_help(client, message):
    """Show help message"""
    help_text = """
🤖 *Available Commands:*

/hello - Greet the bot
/help - Show this help
/ping - Check bot status
/info - Get your info
/echo <text> - Echo your message
/quote <text> - Quote your message

*Examples:*
/echo Hello World
/quote This is a quote
    """
    await client.sendText_(message.get("from"), help_text)


@router.register_command("/ping")
async def cmd_ping(client, message):
    """Check if bot is alive"""
    await client.sendText_(message.get("from"), "🏓 Pong! Bot is online!")


@router.register_command("/info")
async def cmd_info(client, message):
    """Get user information"""
    try:
        contact = await client.getContact_(message.get("from"))
        info_text = f"""
📱 *Your Information:*

Name: {contact.get("name", "N/A")}
Number: {contact.get("number", "N/A")}
Is Business: {contact.get("isBusiness", False)}
        """
        await client.sendText_(message.get("from"), info_text)
    except Exception as e:
        await client.sendText_(message.get("from"), f"Error getting info: {e}")


@router.register_command("/echo")
async def cmd_echo(client, message):
    """Echo the user's message"""
    text = (message.get("body") or "").strip()
    # Remove the command
    echo_text = text.replace("/echo", "").strip()

    if echo_text:
        await client.sendText_(message.get("from"), f"🔊 {echo_text}")
    else:
        await client.sendText_(message.get("from"), "Usage: /echo <text>")


@router.register_command("/quote")
async def cmd_quote(client, message):
    """Quote the user's message"""
    text = (message.get("body") or "").strip()
    quote_text = text.replace("/quote", "").strip()

    if quote_text:
        # Send as markdown quote
        await client.sendText_(message.get("from"), f"> {quote_text}")
    else:
        await client.sendText_(message.get("from"), "Usage: /quote <text>")


async def main():
    async with Create(session="router-example", autoClose=0) as client:

        async def on_message(message):
            if not message.get("fromMe"):
                await router.handle(client, message)

        client.onMessage(on_message)
        client.onStateChange(lambda state: logger.info("State: %s", state))
        logger.info("Listening; press Ctrl+C to close.")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
