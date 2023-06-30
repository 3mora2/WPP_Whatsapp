from WPP_Whatsapp import Create

# start client with your session name
your_session_name = "test"
# Simple
creator = Create(session=your_session_name)

# Hidden Browser
creator = Create(session=your_session_name, headless=True)

# Create With user_data_dir of chrome profile
user_data_dir = "your path here"
creator = Create(session=your_session_name, user_data_dir=user_data_dir)

# folder name when saving tokens
creator = Create(session=your_session_name, folderNameToken="tokens")

# Automatically closes the wppconnect only when scanning the QR code (default 60 seconds, if you want to turn it off, assign 0 or false)
creator = Create(session=your_session_name, autoClose=0)


