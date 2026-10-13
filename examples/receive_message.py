"""Receive message IDs without sending replies. Ctrl+C closes the session."""

from threading import Event

from WPP_Whatsapp import Create


def main():
    with Create("receive-example", autoClose=0) as client:

        def incoming(message):
            print("Received:", message.get("id"))

        client.onMessage(incoming)
        Event().wait()


if __name__ == "__main__":
    main()
