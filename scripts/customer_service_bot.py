"""
Complete Bot Example - Customer Service Bot

This is a comprehensive example showing:
- Full-featured customer service bot
- Multi-language support
- Ticket system
- FAQ handling
- Human handoff
- Analytics tracking
"""

from WPP_Whatsapp import Create
import logging
from datetime import datetime
from typing import Dict, List
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CustomerServiceBot:
    """Complete customer service bot with ticket system"""

    def __init__(self, client):
        self.client = client
        self.tickets: Dict[str, dict] = {}
        self.faq: Dict[str, str] = {}
        self.analytics = {
            'messages_received': 0,
            'tickets_created': 0,
            'tickets_resolved': 0,
            'faq_matches': 0
        }
        self._load_faq()

    def _load_faq(self):
        """Load frequently asked questions"""
        self.faq = {
            'hours': 'We are open Monday-Friday, 9 AM - 6 PM EST',
            'location': 'We are located at 123 Main St, New York, NY 10001',
            'return': 'Our return policy is 30 days from purchase date',
            'shipping': 'We offer free shipping on orders over $50',
            'payment': 'We accept Visa, MasterCard, PayPal, and Apple Pay',
            'tracking': 'You can track your order using the link sent to your email',
            'cancel': 'You can cancel your order within 24 hours of placing it',
            'refund': 'Refunds are processed within 5-7 business days',
            'warranty': 'All products come with a 1-year manufacturer warranty',
            'contact': 'You can reach us at support@example.com or 1-800-123-4567'
        }

    def _find_faq(self, text: str) -> str:
        """Find matching FAQ answer"""
        text = text.lower()

        keywords = {
            'hours': ['hour', 'time', 'open', 'close', 'when'],
            'location': ['where', 'location', 'address', 'store'],
            'return': ['return', 'refund', 'exchange'],
            'shipping': ['ship', 'delivery', 'deliver', 'postage'],
            'payment': ['pay', 'payment', 'card', 'visa', 'mastercard', 'paypal'],
            'tracking': ['track', 'tracking', 'status', 'where is my order'],
            'cancel': ['cancel', 'cancellation'],
            'refund': ['refund', 'money back', 'return money'],
            'warranty': ['warranty', 'guarantee', 'guaranty'],
            'contact': ['contact', 'email', 'phone', 'reach', 'support']
        }

        for key, words in keywords.items():
            if any(word in text for word in words):
                self.analytics['faq_matches'] += 1
                return self.faq.get(key)

        return None

    def _create_ticket(self, user_id: str, message: str) -> str:
        """Create support ticket"""
        ticket_id = f"TKT-{len(self.tickets) + 1:04d}"

        self.tickets[ticket_id] = {
            'user_id': user_id,
            'message': message,
            'created_at': datetime.now(),
            'status': 'open',
            'messages': [message]
        }

        self.analytics['tickets_created'] += 1

        return ticket_id

    def handle_message(self, message: dict):
        """Handle incoming message"""
        try:
            self.analytics['messages_received'] += 1

            user_id = message.get('from')
            text = message.get('body', '').strip()
            is_group = message.get('isGroupMsg', False)

            # Ignore group messages
            if is_group:
                return

            logger.info(f"Message from {user_id}: {text}")

            # Check for commands
            if text.startswith('/'):
                self._handle_command(user_id, text)
                return

            # Check FAQ
            faq_answer = self._find_faq(text)
            if faq_answer:
                response = f"💡 *Helpful Information:*\n\n{faq_answer}\n\nWas this helpful? Reply YES or NO"
                self.client.sendText(user_id, response)
                return

            # Offer to create ticket
            if len(text) > 20:  # Only for longer messages
                ticket_id = self._create_ticket(user_id, text)

                response = f"""
🎫 *Ticket Created*

Ticket ID: `{ticket_id}`
Status: Open

Our support team will respond within 24 hours.

You can check status anytime with: /status {ticket_id}

Is there anything else I can help you with?
                """
                self.client.sendText(user_id, response)
            else:
                # Short message - offer help
                response = """
👋 Hello! How can I help you today?

You can ask about:
• Store hours & location
• Returns & refunds
• Shipping & tracking
• Payments
• Warranties

Or type /help for more options
                """
                self.client.sendText(user_id, response)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self.client.sendText(
                user_id,
                "Sorry, I encountered an error. Please try again later."
            )

    def _handle_command(self, user_id: str, text: str):
        """Handle bot commands"""
        command = text.split()[0].lower()

        if command == '/start':
            self._cmd_start(user_id)
        elif command == '/help':
            self._cmd_help(user_id)
        elif command == '/status':
            self._cmd_status(user_id, text)
        elif command == '/tickets':
            self._cmd_tickets(user_id)
        elif command == '/agent':
            self._cmd_agent(user_id)
        elif command == '/faq':
            self._cmd_faq(user_id)
        else:
            self.client.sendText(
                user_id,
                f"❌ Unknown command: {command}\nType /help for available commands"
            )

    def _cmd_start(self, user_id: str):
        """Handle /start command"""
        response = """
👋 *Welcome to Customer Service Bot!*

I'm here to help you with any questions or issues.

*Quick Help:*
• Ask a question (e.g., "What are your hours?")
• Type /help for all commands
• Type /faq for frequently asked questions

How can I assist you today?
        """
        self.client.sendText(user_id, response)

    def _cmd_help(self, user_id: str):
        """Handle /help command"""
        response = """
📖 *Available Commands:*

/start - Start the bot
/help - Show this help message
/status [ticket_id] - Check ticket status
/tickets - View your tickets
/agent - Connect to human agent
/faq - View FAQ categories
/cancel - Cancel current operation

*Examples:*
/status TKT-0001
/agent (for complex issues)

Just type your question naturally and I'll try to help!
        """
        self.client.sendText(user_id, response)

    def _cmd_status(self, user_id: str, text: str):
        """Handle /status command"""
        parts = text.split()

        if len(parts) < 2:
            # Show all user tickets
            user_tickets = [
                t for t in self.tickets.values()
                if t['user_id'] == user_id
            ]

            if not user_tickets:
                self.client.sendText(user_id, "You have no tickets")
                return

            response = "🎫 *Your Tickets:*\n\n"
            for ticket_id, ticket in user_tickets.items():
                response += f"{ticket_id} - {ticket['status']}\n"

            self.client.sendText(user_id, response)
        else:
            # Show specific ticket
            ticket_id = parts[1]
            ticket = self.tickets.get(ticket_id)

            if not ticket or ticket['user_id'] != user_id:
                self.client.sendText(user_id, f"Ticket {ticket_id} not found")
                return

            response = f"""
🎫 *Ticket Status*

ID: {ticket_id}
Status: {ticket['status']}
Created: {ticket['created_at'].strftime('%Y-%m-%d %H:%M')}
Messages: {len(ticket['messages'])}
            """
            self.client.sendText(user_id, response)

    def _cmd_tickets(self, user_id: str):
        """Handle /tickets command"""
        user_tickets = [
            t for t in self.tickets.values()
            if t['user_id'] == user_id
        ]

        if not user_tickets:
            self.client.sendText(
                user_id,
                "You have no tickets. Type /start to begin."
            )
            return

        response = "🎫 *Your Tickets:*\n\n"
        for ticket_id, ticket in user_tickets.items():
            status_emoji = '🟢' if ticket['status'] == 'open' else '🔴'
            response += f"{status_emoji} {ticket_id} - {ticket['status']}\n"

        self.client.sendText(user_id, response)

    def _cmd_agent(self, user_id: str):
        """Handle /agent command - connect to human agent"""
        # Create urgent ticket
        ticket_id = self._create_ticket(
            user_id,
            "Request to speak with human agent"
        )

        response = f"""
👤 *Human Agent Request*

Ticket ID: `{ticket_id}`
Priority: High

A support agent will contact you within 2 hours during business hours.

For immediate help, call us at 1-800-123-4567
        """
        self.client.sendText(user_id, response)

        # Notify admin (you would implement this)
        logger.info(f"Agent request from {user_id} - Ticket: {ticket_id}")

    def _cmd_faq(self, user_id: str):
        """Handle /faq command"""
        response = """
❓ *Frequently Asked Questions*

Categories:
• Hours - Store hours and availability
• Location - Where to find us
• Returns - Return and exchange policy
• Shipping - Delivery information
• Payment - Payment methods
• Tracking - Order tracking
• Cancel - Order cancellation
• Refund - Refund process
• Warranty - Product warranty
• Contact - How to reach us

Just ask your question naturally!
Example: "What time do you close?"
        """
        self.client.sendText(user_id, response)

    def get_analytics(self) -> dict:
        """Get bot analytics"""
        return self.analytics.copy()


def main():
    logger.info("Starting Customer Service Bot...")

    # Create client
    creator = Create(session="test")
    client = creator.start()

    # Create bot instance
    bot = CustomerServiceBot(client)

    # Message handler
    def on_message(message):
        bot.handle_message(message)

    client.on_message(on_message)

    # State handler
    def on_state_change(state):
        logger.info(f"State: {state}")

        if state == 'CONNECTED':
            logger.info("✅ Bot is connected and ready!")
            logger.info(f"📊 FAQ entries: {len(bot.faq)}")
            logger.info(f"📈 Analytics: {bot.analytics}")

    client.on_state_change(on_state_change)

    logger.info("Bot starting... Scan QR code")
    client.start()


if __name__ == "__main__":
    main()
