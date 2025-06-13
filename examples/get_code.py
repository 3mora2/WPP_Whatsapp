from WPP_Whatsapp import Create

import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)


def catchLinkCode(code: str):
    print(code)



your_session_name = "test_new"
creator = Create(session=your_session_name, catchLinkCode=catchLinkCode,
phoneNumber="your_phone"
                 )

client = creator.start()
creator.loop.run_forever()

