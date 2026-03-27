"""
Rate Limiting Utility for WPPConnect

Provides rate limiting functionality to prevent WhatsApp bans from bulk operations.
"""

import asyncio
import time
from typing import Optional, Callable, Any
from collections import deque
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    """Configuration for rate limiter"""
    calls: int  # Number of calls allowed
    period: float  # Time period in seconds
    delay_between_calls: Optional[float] = None  # Optional delay between calls


class RateLimiter:
    """
    Rate limiter using token bucket algorithm

    Example:
        limiter = RateLimiter(calls=10, period=60)  # 10 calls per minute

        async with limiter:
            await client.sendText("123@c.us", "Hello")
    """

    def __init__(self, calls: int = 10, period: float = 60.0, delay_between_calls: Optional[float] = None):
        """
        Initialize rate limiter

        @param calls: Number of calls allowed in the period
        @param period: Time period in seconds
        @param delay_between_calls: Optional minimum delay between calls in seconds
        """
        self.calls = calls
        self.period = period
        self.delay_between_calls = delay_between_calls
        self.timestamps: deque = deque(maxlen=calls)
        self._lock = asyncio.Lock()
        self._last_call_time: Optional[float] = None

    async def acquire(self):
        """Acquire permission to make a call"""
        async with self._lock:
            now = time.time()

            # Remove old timestamps
            while self.timestamps and self.timestamps[0] <= now - self.period:
                self.timestamps.popleft()

            # Wait if we've exceeded the rate limit
            if len(self.timestamps) >= self.calls:
                wait_time = self.timestamps[0] + self.period - now
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    while self.timestamps and self.timestamps[0] <= time.time() - self.period:
                        self.timestamps.popleft()

            # Apply delay between calls if configured
            if self.delay_between_calls and self._last_call_time:
                elapsed = time.time() - self._last_call_time
                if elapsed < self.delay_between_calls:
                    await asyncio.sleep(self.delay_between_calls - elapsed)

            # Record this call
            self.timestamps.append(time.time())
            self._last_call_time = time.time()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_wait_time(self) -> float:
        """Get time to wait before next call is allowed"""
        now = time.time()
        if len(self.timestamps) < self.calls:
            return 0.0

        wait_time = self.timestamps[0] + self.period - now
        return max(0.0, wait_time)

    @property
    def remaining_calls(self) -> int:
        """Get number of remaining calls in current period"""
        now = time.time()
        while self.timestamps and self.timestamps[0] <= now - self.period:
            self.timestamps.popleft()
        return max(0, self.calls - len(self.timestamps))


class BatchRateLimiter:
    """
    Rate limiter for batch operations with multiple rate limits

    Example:
        limiter = BatchRateLimiter()
        limiter.add_limit('per_second', 1, 1)
        limiter.add_limit('per_minute', 10, 60)

        async with limiter:
            await client.sendText("123@c.us", "Hello")
    """

    def __init__(self):
        self.limiters: dict[str, RateLimiter] = {}

    def add_limit(self, name: str, calls: int, period: float, delay_between_calls: Optional[float] = None):
        """Add a rate limit"""
        self.limiters[name] = RateLimiter(calls, period, delay_between_calls)

    async def acquire(self):
        """Acquire permission from all limiters"""
        for limiter in self.limiters.values():
            await limiter.acquire()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Pre-configured rate limiters for common WhatsApp limits
class WhatsAppRateLimiters:
    """Pre-configured rate limiters for WhatsApp"""

    @staticmethod
    def conservative() -> RateLimiter:
        """
        Conservative rate limiter - safe for all operations
        1 message every 2 seconds, max 20 per minute
        """
        return RateLimiter(calls=20, period=60.0, delay_between_calls=2.0)

    @staticmethod
    def moderate() -> RateLimiter:
        """
        Moderate rate limiter - good for most operations
        1 message every 1 second, max 40 per minute
        """
        return RateLimiter(calls=40, period=60.0, delay_between_calls=1.0)

    @staticmethod
    def aggressive() -> RateLimiter:
        """
        Aggressive rate limiter - use with caution
        1 message every 0.5 seconds, max 60 per minute
        Warning: May trigger WhatsApp anti-spam
        """
        return RateLimiter(calls=60, period=60.0, delay_between_calls=0.5)

    @staticmethod
    def bulk_messages() -> BatchRateLimiter:
        """
        Batch rate limiter for bulk messaging
        Combines multiple limits for safety
        """
        limiter = BatchRateLimiter()
        limiter.add_limit('per_second', 1, 1)  # Max 1 per second
        limiter.add_limit('per_minute', 20, 60)  # Max 20 per minute
        limiter.add_limit('per_hour', 500, 3600)  # Max 500 per hour
        return limiter

    @staticmethod
    def group_operations() -> RateLimiter:
        """
        Rate limiter for group operations
        More conservative to avoid bans
        """
        return RateLimiter(calls=10, period=60.0, delay_between_calls=5.0)

    @staticmethod
    def profile_updates() -> RateLimiter:
        """
        Rate limiter for profile updates
        Very conservative - profile changes are sensitive
        """
        return RateLimiter(calls=5, period=300.0, delay_between_calls=60.0)


# Decorator for rate limiting
def rate_limited(limiter: RateLimiter):
    """
    Decorator to add rate limiting to a function

    Example:
        @rate_limited(WhatsAppRateLimiters.conservative())
        async def send_bulk_messages(messages):
            ...
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            async with limiter:
                return await func(*args, **kwargs)
        return wrapper
    return decorator
