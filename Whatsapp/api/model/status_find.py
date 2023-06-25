"""
SocketState are the possible states of connection between WhatsApp page and phone.
"""


class StatusFind:
    status_ = ['autocloseCalled', 'browserClose', 'desconnectedMobile',
               'inChat', 'isLogged', 'notLogged', 'phoneNotConnected',
               'qrReadError', 'qrReadFail', 'qrReadSuccess', 'serverClose']

    def __init__(self, status=None, session=None):
        self.status = status
        self.session = session

    def __str__(self):
        return f'session: {self.session} status:{self.status}'

    def __repr__(self):
        return f"StatusFind(session={self.session}, status={self.status})"


class CatchQR:
    def __init__(self, qrCode=None, asciiQR=None, attempt=None, urlCode=None):
        self.qrCode = qrCode
        self.asciiQR = asciiQR
        self.attempt = attempt
        self.urlCode = urlCode

    def __str__(self):
        return f'qrCode: {self.qrCode}'

    def is_Not_None(self):
        if self.qrCode and self.asciiQR:
            return True


class LoadingScreen:
    def __init__(self, percent=None, message=None):
        self.percent = percent
        self.message = message

    def __str__(self):
        return f'percent: {self.percent} message:{self.message}'
