"""
Comprehensive Test Suite for WPPConnect Python

Run with: pytest test/ -v
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
import asyncio


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_browser():
    """Mock ThreadsafeBrowser"""
    browser = Mock()
    browser.loop = asyncio.new_event_loop()
    browser.page = Mock()
    browser.page.is_closed = Mock(return_value=False)
    browser.run_threadsafe = Mock(return_value=True)
    browser.page_evaluate = AsyncMock(return_value=True)
    return browser


@pytest.fixture
def mock_client(mock_browser):
    """Mock Whatsapp client"""
    with patch('WPP_Whatsapp.api.Whatsapp.HostLayer.__init__', return_value=None):
        with patch('WPP_Whatsapp.api.Whatsapp.ListenerLayer.__init__', return_value=None):
            from WPP_Whatsapp.api.Whatsapp import Whatsapp

            client = Whatsapp(
                session="test",
                threadsafe_browser=mock_browser,
                page=mock_browser.page
            )
            return client


# ============================================================================
# Test TypedDict Models
# ============================================================================

class TestTypedDictModels:
    """Test TypedDict model classes"""

    def test_send_text_options(self):
        from WPP_Whatsapp.api.model import SendTextOptions

        options: SendTextOptions = {
            "quotedMsg": "msg123",
            "mentions": ["123@c.us"],
            "linkPreview": True
        }
        assert options["quotedMsg"] == "msg123"
        assert options["linkPreview"] is True

    def test_poll_options(self):
        from WPP_Whatsapp.api.model import PollOptions

        options: PollOptions = {
            "selectableCount": 1
        }
        assert options["selectableCount"] == 1

    def test_order_item(self):
        from WPP_Whatsapp.api.model import OrderItem

        item: OrderItem = {
            "productId": "prod123",
            "quantity": 2
        }
        assert item["productId"] == "prod123"
        assert item["quantity"] == 2

    def test_community_options(self):
        from WPP_Whatsapp.api.model import CommunityOptions

        options: CommunityOptions = {
            "description": "Test community",
            "groupIds": ["group1@g.us", "group2@g.us"]
        }
        assert options["description"] == "Test community"
        assert len(options["groupIds"]) == 2

    def test_newsletter_options(self):
        from WPP_Whatsapp.api.model import NewsletterOptions

        options: NewsletterOptions = {
            "description": "Newsletter desc"
        }
        assert options["description"] == "Newsletter desc"

    def test_group_property_options(self):
        from WPP_Whatsapp.api.model import GroupPropertyOptions

        options: GroupPropertyOptions = {
            "property": "restrict",
            "value": True
        }
        assert options["property"] == "restrict"
        assert options["value"] is True


# ============================================================================
# Test Rate Limiter
# ============================================================================

class TestRateLimiter:
    """Test rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        from WPP_Whatsapp.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(calls=5, period=1.0)

        # Should allow first 5 calls immediately
        for _ in range(5):
            await limiter.acquire()

        # 6th call should wait
        import time
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        # Should have waited some time
        assert elapsed > 0.0

    @pytest.mark.asyncio
    async def test_rate_limiter_remaining(self):
        from WPP_Whatsapp.utils.rate_limiter import RateLimiter

        limiter = RateLimiter(calls=10, period=60.0)

        assert limiter.remaining_calls == 10

        await limiter.acquire()
        assert limiter.remaining_calls == 9

    @pytest.mark.asyncio
    async def test_whatsapp_conservative_limiter(self):
        from WPP_Whatsapp.utils.rate_limiter import WhatsAppRateLimiters

        limiter = WhatsAppRateLimiters.conservative()

        assert limiter.calls == 20
        assert limiter.period == 60.0
        assert limiter.delay_between_calls == 2.0

    @pytest.mark.asyncio
    async def test_batch_rate_limiter(self):
        from WPP_Whatsapp.utils.rate_limiter import BatchRateLimiter

        limiter = BatchRateLimiter()
        limiter.add_limit('per_second', 1, 1)
        limiter.add_limit('per_minute', 10, 60)

        await limiter.acquire()  # Should work


# ============================================================================
# Test Batch Operations
# ============================================================================

class TestBatchOperations:
    """Test batch operation functionality"""

    @pytest.mark.asyncio
    async def test_send_bulk_text_success(self, mock_client, mock_browser):
        from WPP_Whatsapp.utils.batch_operations import BatchOperations, BatchStatus

        mock_browser.run_threadsafe = AsyncMock(return_value={"id": "msg123"})

        batch = BatchOperations(mock_client)

        messages = [
            {"to": "123@c.us", "content": "Hello 1"},
            {"to": "456@c.us", "content": "Hello 2"}
        ]

        result = await batch.send_bulk_text(messages, concurrency=1)

        assert result.total == 2
        assert result.successful == 2
        assert result.failed == 0
        assert result.status == BatchStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_send_bulk_text_partial_failure(self, mock_client, mock_browser):
        from WPP_Whatsapp.utils.batch_operations import BatchOperations, BatchStatus

        # First succeeds, second fails
        async def side_effect(*args, **kwargs):
            if not hasattr(side_effect, 'called'):
                side_effect.called = True
                return {"id": "msg123"}
            raise Exception("Failed")

        mock_browser.run_threadsafe = AsyncMock(side_effect=side_effect)

        batch = BatchOperations(mock_client)

        messages = [
            {"to": "123@c.us", "content": "Hello 1"},
            {"to": "456@c.us", "content": "Hello 2"}
        ]

        result = await batch.send_bulk_text(messages, concurrency=1)

        assert result.total == 2
        assert result.successful == 1
        assert result.failed == 1
        assert result.status == BatchStatus.PARTIAL

    @pytest.mark.asyncio
    async def test_delete_many_messages(self, mock_client, mock_browser):
        from WPP_Whatsapp.utils.batch_operations import BatchOperations

        mock_browser.run_threadsafe = AsyncMock(return_value=True)

        batch = BatchOperations(mock_client)

        result = await batch.delete_many_messages(
            chat_id="123@c.us",
            message_ids=["msg1", "msg2", "msg3"],
            concurrency=1
        )

        assert result.total == 3
        assert result.successful == 3


# ============================================================================
# Test Context Manager
# ============================================================================

class TestContextManager:
    """Test context manager functionality"""

    def test_sync_context_manager(self, mock_client):
        """Test synchronous context manager"""

        with mock_client as client:
            assert client is mock_client

        # Should have called close
        assert mock_client.ThreadsafeBrowser.sync_close.called

    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_client):
        """Test asynchronous context manager"""

        # Mock the close_async to avoid await on Mock
        mock_client.close_async = AsyncMock()

        async with mock_client as client:
            assert client is mock_client

        # Should have called close_async
        assert mock_client.close_async.called


# ============================================================================
# Test Valid ChatId
# ============================================================================

class TestValidChatId:
    """Test chatId validation"""

    def test_valid_phone_number(self):
        from WPP_Whatsapp.api.layers.HostLayer import HostLayer

        result = HostLayer.valid_chatId("1234567890")
        assert result == "1234567890@c.us"

    def test_valid_group_id(self):
        from WPP_Whatsapp.api.layers.HostLayer import HostLayer

        result = HostLayer.valid_chatId("1234567890-987654321")
        assert result == "1234567890-987654321@g.us"

    def test_already_formatted(self):
        from WPP_Whatsapp.api.layers.HostLayer import HostLayer

        result = HostLayer.valid_chatId("1234567890@c.us")
        assert result == "1234567890@c.us"

    def test_with_plus_sign(self):
        from WPP_Whatsapp.api.layers.HostLayer import HostLayer

        result = HostLayer.valid_chatId("+1234567890")
        assert result == "1234567890@c.us"

    def test_invalid_format(self):
        from WPP_Whatsapp.api.layers.HostLayer import HostLayer

        with pytest.raises(ValueError, match="Invalid chatId suffix"):
            HostLayer.valid_chatId("invalid@chat")

    def test_empty_chatId(self):
        from WPP_Whatsapp.api.layers.HostLayer import HostLayer

        with pytest.raises(ValueError, match="chatId cannot be empty"):
            HostLayer.valid_chatId("")

    def test_broadcast_suffix(self):
        from WPP_Whatsapp.api.layers.HostLayer import HostLayer

        result = HostLayer.valid_chatId("status@broadcast")
        assert result == "status@broadcast"


# ============================================================================
# Test Community Layer
# ============================================================================

class TestCommunityLayer:
    """Test community operations"""

    @pytest.mark.asyncio
    async def test_create_community(self, mock_browser):
        from WPP_Whatsapp.api.layers.CommunityLayer import CommunityLayer

        mock_browser.page_evaluate = AsyncMock(return_value="community_id@g.us")

        with patch.object(CommunityLayer, '__init__', lambda x: None):
            community = CommunityLayer()
            community.ThreadsafeBrowser = mock_browser
            community.page = mock_browser.page

            result = await community.createCommunity_(
                name="Test Community",
                description="Test Description",
                groupIds=["group1@g.us", "group2@g.us"]
            )

            assert result == "community_id@g.us"
            mock_browser.page_evaluate.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_community_participants(self, mock_browser):
        from WPP_Whatsapp.api.layers.CommunityLayer import CommunityLayer

        mock_browser.page_evaluate = AsyncMock(
            return_value=["123@c.us", "456@c.us"]
        )

        with patch.object(CommunityLayer, '__init__', lambda x: None):
            community = CommunityLayer()
            community.ThreadsafeBrowser = mock_browser
            community.page = mock_browser.page

            result = await community.getCommunityParticipants_("community@g.us")

            assert len(result) == 2
            assert "123@c.us" in result


# ============================================================================
# Test Newsletter Layer
# ============================================================================

class TestNewsletterLayer:
    """Test newsletter operations"""

    @pytest.mark.asyncio
    async def test_create_newsletter(self, mock_browser):
        from WPP_Whatsapp.api.layers.NewsletterLayer import NewsletterLayer

        mock_browser.page_evaluate = AsyncMock(
            return_value={"id": "newsletter123"}
        )

        with patch.object(NewsletterLayer, '__init__', lambda x: None):
            newsletter = NewsletterLayer()
            newsletter.ThreadsafeBrowser = mock_browser
            newsletter.page = mock_browser.page

            result = await newsletter.createNewsletter_(
                name="Test Newsletter",
                options={"description": "Test"}
            )

            assert result["id"] == "newsletter123"


# ============================================================================
# Test Poll Messages
# ============================================================================

class TestPollMessages:
    """Test poll message functionality"""

    @pytest.mark.asyncio
    async def test_send_poll_message(self, mock_browser):
        from WPP_Whatsapp.api.layers.SenderLayer import SenderLayer
        from WPP_Whatsapp.api.model import PollOptions

        mock_browser.page_evaluate = AsyncMock(return_value=True)

        sender = SenderLayer()
        sender.ThreadsafeBrowser = mock_browser
        sender.page = mock_browser.page
        sender.valid_chatId = lambda x: x + "@c.us" if "@" not in x else x

        options: PollOptions = {"selectableCount": 1}

        result = await sender.sendPollMessage_(
            chatId="123",
            name="Favorite color?",
            choices=["Red", "Blue", "Green"],
            options=options
        )

        assert result is True
        mock_browser.page_evaluate.assert_called_once()


# ============================================================================
# Test Catalog Layer
# ============================================================================

class TestCatalogLayer:
    """Test catalog operations"""

    @pytest.mark.asyncio
    async def test_create_product(self, mock_browser):
        from WPP_Whatsapp.api.layers.CatalogLayer import CatalogLayer

        mock_browser.page_evaluate = AsyncMock(
            return_value={"id": "product123"}
        )

        with patch.object(CatalogLayer, '__init__', lambda x: None):
            catalog = CatalogLayer()
            catalog.ThreadsafeBrowser = mock_browser
            catalog.page = mock_browser.page

            result = await catalog.createProduct_(
                name="Test Product",
                image="data:image/jpeg;base64,test",
                description="Test Description",
                price=99.99,
                isHidden=False,
                url="https://example.com",
                retailerId="PROD-001",
                currency="USD"
            )

            assert result["id"] == "product123"


# ============================================================================
# Test Profile Layer
# ============================================================================

class TestProfileLayer:
    """Test profile operations"""

    @pytest.mark.asyncio
    async def test_get_profile_name(self, mock_browser):
        from WPP_Whatsapp.api.layers.ProfileLayer import ProfileLayer

        mock_browser.page_evaluate = AsyncMock(
            return_value="John Doe"
        )

        with patch.object(ProfileLayer, '__init__', lambda x: None):
            profile = ProfileLayer()
            profile.ThreadsafeBrowser = mock_browser
            profile.page = mock_browser.page

            result = await profile.getProfileName_()

            assert result == "John Doe"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_complete_messaging_workflow(self, mock_browser):
        """Test complete messaging workflow"""
        from WPP_Whatsapp.utils.batch_operations import BatchOperations
        from WPP_Whatsapp.utils.rate_limiter import WhatsAppRateLimiters
        from WPP_Whatsapp.api.Whatsapp import Whatsapp

        # Create proper mock client
        with patch.object(Whatsapp, '__init__', lambda x, *args, **kwargs: None):
            mock_client = Whatsapp.__new__(Whatsapp)
            mock_client.ThreadsafeBrowser = mock_browser
            mock_browser.run_threadsafe = AsyncMock(return_value={"id": "msg123"})

            # Setup
            limiter = WhatsAppRateLimiters.conservative()
            batch = BatchOperations(mock_client, limiter)

            # Send messages
            messages = [
                {"to": "123@c.us", "content": "Hello 1"},
                {"to": "456@c.us", "content": "Hello 2"},
            ]

            result = await batch.send_bulk_text(messages, concurrency=1)

            # Verify
            assert result.total == 2
            assert result.successful >= 1


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
