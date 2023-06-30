import logging

useragentOverride = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36'
whatsappUrl = 'https://web.whatsapp.com'
chromiumArgs = [
    '--log-level=3',
    '--start-maximized',
    '--no-default-browser-check',
    '--disable-site-isolation-trials',
    '--no-experiments',
    '--ignore-gpu-blacklist',
    '--ignore-certificate-errors',
    '--ignore-certificate-errors-spki-list',
    '--disable-gpu',
    '--disable-extensions',
    '--disable-default-apps',
    '--enable-features=NetworkService',
    '--disable-setuid-sandbox',
    '--no-sandbox',
    # Extras
    '--disable-webgl',
    '--disable-infobars',
    '--window-position=0,0',
    '--ignore-certifcate-errors',
    '--ignore-certifcate-errors-spki-list',
    '--disable-threaded-animation',
    '--disable-threaded-scrolling',
    '--disable-in-process-stack-traces',
    '--disable-histogram-customizer',
    '--disable-gl-extensions',
    '--disable-composited-antialiasing',
    '--disable-canvas-aa',
    '--disable-3d-apis',
    '--disable-accelerated-2d-canvas',
    '--disable-accelerated-jpeg-decoding',
    '--disable-accelerated-mjpeg-decode',
    '--disable-app-list-dismiss-on-blur',
    '--disable-accelerated-video-decode',
    '--disable-dev-shm-usage',
]


def defaultLogger():
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S')
    logger = logging.getLogger(name="WPP_Whatsapp")
    return logger


Logger = defaultLogger()

defaultOptions = {
    "folderNameToken": r"E:\Projects\Python\_Libs_\tokens",
    "headless": True,
    "devtools": False,
    "useChrome": True,
    "debug": False,
    "logQR": True,
    "browserWS": '',
    "browserArgs": [''],
    "puppeteerOptions": {},
    "disableWelcome": False,
    "updatesLog": True,
    "autoClose": 0,
    "deviceSyncTimeout": 180000,
    "createPathFileToken": True,
    "waitForLogin": True,
    "logger": defaultLogger(),
    "tokenStore": 'file',
    'whatsappVersion': '2.2326.x',
    'deviceName': False,
    'linkPreviewApiServers': None,
    'disableGoogleAnalytics': True,
    'googleAnalyticsId': None,
    'poweredBy': 'WPPConnect',
}
