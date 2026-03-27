"""
Example: Using Context Manager

This example demonstrates how to use the context manager for automatic cleanup.
"""

from WPP_Whatsapp import Create


def main():
    print("=== Example 1: Sync Context Manager ===")

    # Sync context manager - automatically closes on exit
    with Create(session="context_example") as client:
        client.waitForLogin()

        # Send a message
        result = client.sendText("1234567890@c.us", "Hello from context manager!")
        print(f"Message sent: {result}")

        # No need to call client.close() - it's automatic!

    print("Session automatically closed!\n")

    print("=== Example 2: Async Context Manager ===")

    import asyncio

    async def async_example():
        async with Create(session="async_context_example") as client:
            client.waitForLogin()

            # Send a message
            result = await client.sendText_("1234567890@c.us", "Hello from async context manager!")
            print(f"Message sent: {result}")

            # No need to call await client.close_async() - it's automatic!

    # asyncio.run(async_example())

    print("Async session automatically closed!\n")

    print("=== Example 3: With Error Handling ===")

    try:
        with Create(session="error_example") as client:
            client.waitForLogin()

            # This might fail
            result = client.sendText("invalid_chat", "This will fail")
            print(f"Message sent: {result}")

    except Exception as e:
        print(f"Error occurred: {e}")
        print("But session was still closed properly!")

    print("\nAll examples completed!")


if __name__ == "__main__":
    main()
