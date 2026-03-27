from WPP_Whatsapp import Create
import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)

your_session_name = "test"
creator = Create(session=your_session_name, autoClose=0)
creator.start()
