import os
import random
import asyncio
import sqlite3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from config import API_ID, API_HASH, BOT_TOKEN, START_MSG, IMG_LINKS, ADMIN_ID

# --- DATABASE SETUP ---
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
db.commit()

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

def get_total_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]

# --- HEALTH CHECK SERVER ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running")

def run_health_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- BOT CLIENT ---
bot = Client("auto_approve_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    add_user(message.from_user.id)
    photo = random.choice(IMG_LINKS)
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✨ ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ", url="https://t.me/Hindi_Tv_Verse"),
            InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇꜱ", url="https://t.me/AJ_TVSERIAL")
        ],
        [InlineKeyboardButton("🛠 sᴜᴘᴘᴏʀᴛ ᴀᴅᴍɪɴ", url="https://t.me/SerialVerse_support")]
    ])
    await message.reply_photo(
        photo=photo,
        caption=START_MSG.format(name=message.from_user.first_name),
        reply_markup=buttons
    )

@bot.on_chat_join_request()
async def approve_request(client, request: ChatJoinRequest):
    add_user(request.from_user.id)
    try:
        await client.approve_chat_join_request(request.chat.id, request.from_user.id)
        await client.send_photo(
            chat_id=request.from_user.id,
            photo=random.choice(IMG_LINKS),
            caption=f"<b>ʜᴇʟʟᴏ {request.from_user.first_name} ✨,\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ ʜᴀs ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n\n📍ᴊᴏɪɴ ᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ᴄʜᴀɴɴᴇʟ - @Hindi_Tv_Verse & @AJ_TVSERIAL"
        )
    except Exception as e:
        print(f"Error: {e}")

# --- ADMIN FEATURES ---

@bot.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats(client, message):
    total = get_total_users()
    await message.reply_text(f"📊 **Bot Statistics**\n\nTotal Users in DB: `{total}`")

@bot.on_message(filters.command("broadcast") & filters.user(ADMIN_ID) & filters.reply)
async def broadcast(client, message):
    all_users = get_all_users()
    broadcast_msg = message.reply_to_message
    sts = await message.reply_text(f"🚀 **Broadcast Started...**\nSending to {len(all_users)} users.")
    
    success = 0
    blocked = 0
    deleted = 0
    failed = 0

    for user_id in all_users:
        try:
            await broadcast_msg.copy(save_display_name=True, chat_id=user_id)
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await broadcast_msg.copy(save_display_name=True, chat_id=user_id)
            success += 1
        except UserIsBlocked:
            blocked += 1
        except InputUserDeactivated:
            deleted += 1
        except Exception:
            failed += 1

    await sts.edit(f"✅ **Broadcast Completed!**\n\n✨ Success: `{success}`\n🚫 Blocked: `{blocked}`\n💀 Deleted: `{deleted}`\n❌ Failed: `{failed}`")

# --- MAIN ---
if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    print("🔥 Bot Started Successfully!")
    bot.run()
