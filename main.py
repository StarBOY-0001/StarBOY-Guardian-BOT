import os
import re
from pyrogram import Client, filters
from pyrogram.types import Message

# 1. Configuration (Loaded via Environment Variables for Security)
API_ID = int(os.environ.get("API_ID", 12345))          # Get from my.telegram.org
API_HASH = os.environ.get("API_HASH", "your_hash")     # Get from my.telegram.org
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")   # Get from @BotFather

app = Client("group_guardian", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Robust regex to detect URLs/links
URL_PATTERN = r"(https?:\/\/[^\s]+|(www\.[^\s]+)|[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,5})(\/[^\s]*)?"

async def is_sender_admin(message: Message) -> bool:
    """Helper to ensure we do not accidentally delete admin or owner messages"""
    if not message.chat or message.chat.type.name not in ["SUPERGROUP", "GROUP"]:
        return False
    try:
        member = await app.get_chat_member(message.chat.id, message.from_user.id)
        return member.status.name in ["OWNER", "ADMINISTRATOR"]
    except Exception:
        return False

# FEATURE 1, 2, & 3: Watch Incoming Messages (Media, Links, Stickers)
@app.on_message(filters.group & ~filters.service)
async def monitor_messages(client: Client, message: Message):
    if not message.from_user or await is_sender_admin(message):
        return

    should_delete = False

    # A. Check for Media (Photos, Videos, Voice, Documents, Animations/GIFs)
    if any([message.photo, message.video, message.document, message.voice, message.audio, message.animation]):
        should_delete = True

    # B. Check for Stickers 
    # Note: Telegram's API doesn't label stickers as "adult" natively. To prevent explicit 
    # custom sticker packs, the industry standard is to block all sticker types entirely.
    elif message.sticker:
        should_delete = True

    # C. Check for URLs / Links (Plain text and formatted text hyperlinks)
    else:
        combined_text = (message.text or "") + " " + (message.caption or "")
        if re.search(URL_PATTERN, combined_text):
            should_delete = True
        elif message.entities or message.caption_entities:
            entities = message.entities or message.caption_entities or []
            for entity in entities:
                if entity.type.name in ["URL", "TEXT_LINK"]:
                    should_delete = True
                    break

    if should_delete:
        try:
            await message.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")

# FEATURE 4: Watch Edited Messages (Instantly delete any modification)
@app.on_edited_message(filters.group)
async def monitor_edits(client: Client, message: Message):
    if not message.from_user or await is_sender_admin(message):
        return

    try:
        await message.delete()
    except Exception as e:
        print(f"Error deleting edited message: {e}")

if __name__ == "__main__":
    print("Guardian Bot is actively protecting your group...")
    app.run()
