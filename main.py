from fastapi import FastAPI
import uvicorn
import os, time
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv
import asyncio

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")

if not API_ID or not API_HASH or not STRING_SESSION:
    raise SystemExit("Set API_ID, API_HASH, and STRING_SESSION in .env first.")

# Telegram client
client = TelegramClient(
    StringSession(STRING_SESSION), 
    API_ID, 
    API_HASH,
    flood_sleep_threshold=10
)

# Duplicate detection
_recent = {}
DEDUP_WINDOW_SEC = 10

def _is_dup(chat_id, user_id):
    now = time.time()
    key = (chat_id, user_id)
    last = _recent.get(key)
    _recent[key] = now
    for k, t in list(_recent.items()):
        if now - t > 300:
            del _recent[k]
    return last is not None and (now - last) < DEDUP_WINDOW_SEC

# Listen to all joins in all chats
@client.on(events.ChatAction(chats=None))
async def on_action(event):
    try:
        if not (event.user_joined or event.user_added):
            return

        chat = await event.get_chat()
        chat_title = getattr(chat, "title", None) or getattr(chat, "username", None) or str(event.chat_id)

        new_users = []
        if event.user_joined:
            u = await event.get_user()
            if u:
                new_users.append(u)
        if event.user_added:
            for u in (event.users or []):
                new_users.append(u)

        adder = getattr(event, "added_by", None)
        try:
            if event.user_added and adder is None:
                adder = await event.get_user()
        except:
            pass

        for u in new_users:
            if _is_dup(event.chat_id, u.id):
                continue

            name = " ".join(filter(None, [u.first_name, u.last_name])) or "(no name)"
            username = f"@{u.username}" if u.username else "(no username)"
            when = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            added_by_line = ""
            if event.user_added and adder:
                adder_name = " ".join(filter(None, [getattr(adder, "first_name", ""), getattr(adder, "last_name", "")])).strip()
                adder_user = f"@{getattr(adder, 'username', '')}" if getattr(adder, "username", None) else "(no username)"
                added_by_line = f"\n• Added by: {adder_name} {adder_user} (id {adder.id})"

            msg = (
                "🔔 New member joined\n"
                f"• Group: {chat_title}\n"
                f"• Name: {name} {username}\n"
                f"• ID: {u.id}\n"
                f"• When: {when}{added_by_line}"
            )

            await client.send_message("me", msg)

    except Exception as e:
        print(f"Error in on_action: {e}")

# FastAPI app
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Start the Telegram client in background
    asyncio.create_task(client.start())

@app.get("/")
async def read_root():
    return {"status": "Bot is running"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
