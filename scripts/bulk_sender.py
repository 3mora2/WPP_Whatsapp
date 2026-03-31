"""
Bulk Sender with Rate Limiting

This example demonstrates:
- Safe bulk messaging
- Rate limiting to avoid bans
- Progress tracking
- Error handling
- Batch operations
"""

from WPP_Whatsapp import Create
import time
import logging
from typing import List, Dict
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BulkSender:
    """Safe bulk message sender with rate limiting"""

    def __init__(self, client, messages_per_minute=20):
        self.client = client
        self.delay = 60 / messages_per_minute  # Delay between messages
        self.stats = {
            'sent': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None
        }

    def send_bulk(self, contacts: List[str], message: str) -> Dict:
        """
        Send message to multiple contacts safely

        Args:
            contacts: List of phone numbers or chat IDs
            message: Message to send
        """
        self.stats['start_time'] = datetime.now()
        self.stats['sent'] = 0
        self.stats['failed'] = 0

        logger.info(f"Starting bulk send to {len(contacts)} contacts...")
        logger.info(f"Rate limit: 1 message per {self.delay:.1f} seconds")

        for i, contact in enumerate(contacts, 1):
            try:
                # Format contact if it's just a number
                if '@' not in contact:
                    contact = f"{contact}@c.us"

                # Check if number exists
                logger.info(f"[{i}/{len(contacts)}] Sending to {contact}...")

                # Send message
                self.client.sendText(contact, message)
                self.stats['sent'] += 1

                logger.info(f"✓ Sent to {contact}")

                # Rate limiting delay
                if i < len(contacts):
                    time.sleep(self.delay)

            except Exception as e:
                self.stats['failed'] += 1
                logger.error(f"✗ Failed to send to {contact}: {e}")

        self.stats['end_time'] = datetime.now()
        self._print_summary()

        return self.stats

    def send_bulk_with_personalization(
        self,
        contacts: List[Dict[str, str]],
        template: str
    ) -> Dict:
        """
        Send personalized messages

        Args:
            contacts: List of dicts with 'number' and optional fields
            template: Message template with {placeholders}

        Example:
            contacts = [
                {'number': '1234567890', 'name': 'John'},
                {'number': '0987654321', 'name': 'Jane'}
            ]
            template = "Hello {name}! How are you?"
        """
        self.stats['start_time'] = datetime.now()
        self.stats['sent'] = 0
        self.stats['failed'] = 0

        logger.info(f"Starting personalized bulk send to {len(contacts)} contacts...")

        for i, contact_data in enumerate(contacts, 1):
            try:
                number = contact_data.get('number')
                if not number:
                    logger.warning(f"Skipping contact without number: {contact_data}")
                    continue

                if '@' not in number:
                    number = f"{number}@c.us"

                # Personalize message
                message = template.format(**contact_data)

                logger.info(f"[{i}/{len(contacts)}] Sending to {number}...")

                self.client.sendText(number, message)
                self.stats['sent'] += 1

                logger.info(f"✓ Sent to {number}")

                # Rate limiting delay
                if i < len(contacts):
                    time.sleep(self.delay)

            except Exception as e:
                self.stats['failed'] += 1
                logger.error(f"✗ Failed: {e}")

        self.stats['end_time'] = datetime.now()
        self._print_summary()

        return self.stats

    def _print_summary(self):
        """Print sending summary"""
        duration = self.stats['end_time'] - self.stats['start_time']

        summary = f"""
╔════════════════════════════════════════╗
║        BULK SEND SUMMARY               ║
╠════════════════════════════════════════╣
║ Total Contacts: {self.stats['sent'] + self.stats['failed']:>6}           ║
║ Sent Successfully: {self.stats['sent']:>6}           ║
║ Failed: {self.stats['failed']:>6}               ║
║ Duration: {duration.total_seconds():>6.1f} seconds        ║
╚════════════════════════════════════════╝
        """
        logger.info(summary)


def main():
    logger.info("Starting Bulk Sender Example...")

    # Create client
    creator = Create(session="test")
    client = creator.start()

    # Example 1: Simple bulk send
    def example_simple_bulk():
        contacts = [
            "1234567890",
            "0987654321",
            "1122334455"
        ]

        message = """
🎉 Special Offer!

Get 50% off on all products this week!
Use code: SAVE50

Visit our store: https://example.com

Reply STOP to unsubscribe
        """

        sender = BulkSender(client, messages_per_minute=15)
        sender.send_bulk(contacts, message)

    # Example 2: Personalized messages
    def example_personalized():
        contacts = [
            {'number': '1234567890', 'name': 'John', 'product': 'Widget'},
            {'number': '0987654321', 'name': 'Jane', 'product': 'Gadget'},
            {'number': '1122334455', 'name': 'Bob', 'product': 'Gizmo'}
        ]

        template = """
Hi {name}! 👋

Great news about the {product} you interested in!
It's now on sale with 30% discount.

Order now: https://example.com/{product}

Best regards,
Your Team
        """

        sender = BulkSender(client, messages_per_minute=20)
        sender.send_bulk_with_personalization(contacts, template)

    # Wait for client to be ready
    def on_state_change(state):
        logger.info(f"State: {state}")
        if state == 'CONNECTED':
            logger.info("Bot connected! Starting bulk send in 5 seconds...")
            time.sleep(5)

            # Run example
            example_personalized()

            # Or run simple bulk
            # example_simple_bulk()

    client.on_state_change(on_state_change)

    logger.info("Bot starting... Scan QR code")
    client.start()


if __name__ == "__main__":
    main()
