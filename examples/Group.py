from WPP_Whatsapp import Create

import logging

logger = logging.getLogger(name="WPP_Whatsapp")
logger.setLevel(logging.DEBUG)

# start client with your session name
your_session_name = "test"
creator = Create(session=your_session_name, browser="chrome", install=False)
client = creator.start()
# Now scan Whatsapp Qrcode in browser

# check state of login
if creator.state != 'CONNECTED':
    raise Exception(creator.state)

resp = client.createGroup("grp_n43e5ame", ["20109969@c.us"])
group_jid = resp.get("gid") or resp.get("id")
# client.addParticipant(group_jid.get('_serialized'), "*****@c.us")