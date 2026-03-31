"""
Advanced Message Handler Example

This example demonstrates:
- Command routing system
- Message middleware
- Context management
- Error handling
- Logging
"""

from WPP_Whatsapp import Create
import logging
from functools import wraps
from typing import Callable, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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
        text = message.get('body', '').strip()
        if not text:
            return

        # Check if it's a command
        if text.startswith('/'):
            command = text.split()[0].lower()
            handler = self.handlers.get(command)

            if handler:
                try:
                    await handler(client, message)
                except Exception as e:
                    logger.error(f"Error in command {command}: {e}")
                    client.sendText(
                        message.get('from'),
                        f"❌ Error executing command: {str(e)}"
                    )
            else:
                client.sendText(
                    message.get('from'),
                    f"❌ Unknown command: {command}\nUse /help for available commands"
                )


# Create router instance
router = MessageRouter()


# Middleware: Log all messages
async def log_messages(client, message):
    logger.info(f"Message from {message.get('from')}: {message.get('body')}")
    return True  # Continue processing


# Middleware: Ignore group messages
async def ignore_groups(client, message):
    if message.get('isGroupMsg'):
        return False  # Stop processing
    return True


# Middleware: Block specific users
BLOCKED_USERS = ['blocked_number@c.us']
async def check_blocked(client, message):
    if message.get('from') in BLOCKED_USERS:
        return False
    return True


# Register middleware
router.use(log_messages)
router.use(ignore_groups)
router.use(check_blocked)


# Command Handlers
@router.register_command('/hello')
async def cmd_hello(client, message):
    """Greet the user"""
    client.sendText(message.get('from'), f"👋 Hello! How can I help you?")


@router.register_command('/help')
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
    client.sendText(message.get('from'), help_text)


@router.register_command('/ping')
async def cmd_ping(client, message):
    """Check if bot is alive"""
    client.sendText(message.get('from'), "🏓 Pong! Bot is online!")


@router.register_command('/info')
async def cmd_info(client, message):
    """Get user information"""
    try:
        contact = client.getContact(message.get('from'))
        info_text = f"""
📱 *Your Information:*

Name: {contact.get('name', 'N/A')}
Number: {contact.get('number', 'N/A')}
Is Business: {contact.get('isBusiness', False)}
        """
        client.sendText(message.get('from'), info_text)
    except Exception as e:
        client.sendText(message.get('from'), f"Error getting info: {e}")


@router.register_command('/echo')
async def cmd_echo(client, message):
    """Echo the user's message"""
    text = message.get('body', '').strip()
    # Remove the command
    echo_text = text.replace('/echo', '').strip()

    if echo_text:
        client.sendText(message.get('from'), f"🔊 {echo_text}")
    else:
        client.sendText(message.get('from'), "Usage: /echo <text>")


@router.register_command('/quote')
async def cmd_quote(client, message):
    """Quote the user's message"""
    text = message.get('body', '').strip()
    quote_text = text.replace('/quote', '').strip()

    if quote_text:
        # Send as markdown quote
        client.sendText(message.get('from'), f"> {quote_text}")
    else:
        client.sendText(message.get('from'), "Usage: /quote <text>")


# Main bot setup
def main():
    logger.info("Starting Advanced Message Handler Bot...")

    # Create client
    creator = Create(session="test")
    client = creator.start()

    # Message handler
    def on_message(message):
        import asyncio
        asyncio.run(router.handle(client, message))

    client.on_message(on_message)

    # State change handler
    def on_state_change(state):
        logger.info(f"State changed: {state}")

    client.on_state_change(on_state_change)

    logger.info("Bot is running! Scan QR code to start...")
    client.start()


if __name__ == "__main__":
    main()
