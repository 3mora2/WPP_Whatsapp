from WPP_Whatsapp import Create


def catchQR(qrCode: str, asciiQR: str, attempt: int, urlCode: str):
    """
    qrCode:"data:image/png;base64,",
    asciiQR:"",
    attempt:1,
    urlCode:"2@242",
    """
    print(qrCode[:500])
    print(asciiQR)
    print(attempt)
    print(urlCode)


your_session_name = "test_new"
creator = Create(session=your_session_name, catchQR=catchQR,
                 logQR=True  # Return value of asciiQR, you can print qrcode in console
                 )

client = creator.start()
