import threading
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget
try:
    from WPP_Whatsapp import Create
except (ModuleNotFoundError, ImportError):
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from WPP_Whatsapp import Create

import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.creators = []

    def initUI(self):
        self.setWindowTitle('WhatsApp Messenger')
        self.setGeometry(100, 100, 400, 300)

        self.session_input = QLineEdit(self)
        self.session_input.move(20, 20)
        self.session_input.resize(360, 30)
        self.session_input.setPlaceholderText("Enter session name")

        self.phone_input = QLineEdit(self)
        self.phone_input.move(20, 70)
        self.phone_input.resize(360, 30)
        self.phone_input.setPlaceholderText("Enter phone number")

        self.message_input = QLineEdit(self)
        self.message_input.move(20, 120)
        self.message_input.resize(360, 30)
        self.message_input.setPlaceholderText("Enter message")

        self.send_button = QPushButton('Send Message', self)
        self.send_button.move(20, 170)
        self.send_button.clicked.connect(self.send_message)

    def send_message(self):
        session_name = self.session_input.text()
        phone_number = self.phone_input.text()
        message = self.message_input.text()

        # Start the WhatsApp client in a separate thread
        threading.Thread(target=self.start_whatsapp_client, args=(session_name, phone_number, message)).start()

    def start_whatsapp_client(self, session_name, phone_number, message):
        creator = Create(session=session_name)
        try:
            self.creators.append(creator)
            client = creator.start()
            if creator.state != 'CONNECTED':
                raise Exception(creator.state)

            # Send the message
            result = client.sendText(phone_number, message)
            print("Message sent successfully:", result)
            creator.sync_close()
        except Exception as e:
            print("Exception", e)
        finally:
            creator.client.isClosed = True

    def closeEvent(self, a0):
        # Ensure Close all
        for creator in self.creators:
            creator.client.isClosed = True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
