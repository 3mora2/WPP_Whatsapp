"""Read a caller-selected chat; no automatic outbound messages."""

import argparse

from WPP_Whatsapp import Create


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chat_id")
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    with Create("history-example", autoClose=0) as client:
        messages = client.getMessages(args.chat_id, {"count": args.count})
        print("Messages:", len(messages))
        for message in messages:
            print(message.get("id"))


if __name__ == "__main__":
    main()
