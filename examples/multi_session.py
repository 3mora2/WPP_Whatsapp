from WPP_Whatsapp import Create
import threading

Session = dict()

first_name = "first_session"
second_name = "second_session"


def send_message(session, message, phone_number):
    print("start:", session)
    Session[session] = Create(session=session, autoClose=0, browser="firefox")
    client = Session[session].start()
    result = client.sendText(phone_number, message)
    print(result)
    Session[session].close()


th1 = threading.Thread(target=send_message, args=(first_name, "hello from wpp", "201016708170"))
th1.start()
th2 = threading.Thread(target=send_message, args=(second_name, "hello from wpp", "201016708170"))
th2.start()
