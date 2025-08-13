# create_string_session.py
import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

load_dotenv()  # reads your .env with API_ID and API_HASH

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "selfbot")  # uses the same session you already have

if not API_ID or not API_HASH:
    raise SystemExit("Make sure API_ID and API_HASH are in .env")

# This will load your existing local session file (selfbot.session) and print a string
with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
    string = StringSession.save(client.session)
    print("\n--- COPY THIS STRING AND KEEP IT SECRET ---\n")
    print(string)
    print("\n--- END ---\n")
