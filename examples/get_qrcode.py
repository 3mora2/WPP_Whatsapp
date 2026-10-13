"""Show login in the browser; do not print secret QR/login payloads."""

from threading import Event

from WPP_Whatsapp import Create


def qr_ready(qrCode, asciiQR, attempt, urlCode):
    print("QR ready in the browser; attempt:", attempt)


def main():
    with Create("qr-example", autoClose=0, catchQR=qr_ready, logQR=False) as client:
        print("Login finished; chats:", len(client.listChats({"count": 5})))
        Event().wait()


if __name__ == "__main__":
    main()
