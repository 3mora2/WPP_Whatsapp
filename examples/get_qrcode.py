from WPP_Whatsapp import Create

import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)


def catchQR(qrCode: str, asciiQR: str, attempt: int, urlCode: str):
    """
    qrCode:"data:image/png;base64,",
    asciiQR:"",
    attempt:1,
    urlCode:"2@242",
    """
    print(qrCode)
    print(asciiQR)
    print(attempt)
    print(urlCode)


your_session_name = "test_new"
creator = Create(session=your_session_name, catchQR=catchQR,
                 logQR=True  # Return value of asciiQR, you can print qrcode in console
                 )

client = creator.start()
creator.loop.run_forever()

# multi catchQR

# class Lablab:
#
#     def catchQR(self, qrCode: str, asciiQR: str, attempt: int, urlCode: str):
#         """
#         qrCode:"data:image/png;base64,",
#         asciiQR:"",
#         attempt:1,
#         urlCode:"2@242",
#         """
#         print("from Lablab", qrCode)
#         print("from Lablab", asciiQR)
#         print("from Lablab", attempt)
#         print("from Lablab", urlCode)
#
#
# your_session_name = "test_new"
# creator = Create(session=your_session_name,
#                  catchQR=lambda *args, **kwargs: (catchQR(*args, **kwargs), Lablab().catchQR(*args, **kwargs)),
#                  logQR=True  # Return value of asciiQR, you can print qrcode in console
#                  )
#
# client = creator.start()
# creator.loop.run_forever()
