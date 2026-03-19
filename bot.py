import os
import random
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from config import API_ID, API_HASH, BOT_TOKEN, START_MSG, IMG_LINKS, ADMIN_ID

# --- SAFE MONGODB IMPORT ---
try:
    from pymongo import MongoClient
    MONGO = True
except:
    MONGO = False

# --- DATABASE SETUP ---
if MONGO and os.environ.get("MONGO_DB_URI"):
    mongo_client = MongoClient(os.environ.get("MONGO_DB_URI"))
    db = mongo_client["telegram_bot"]
    users_col = db["users"]

    def add_user(user_id):
        users_col.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

    def remove_user(user_id):
        users_col.delete_one({"user_id": user_id})

    def get_total_users():
        return users_col.count_documents({})

    def get_all_users():
        return [u["user_id"] for u in users_col.find({}, {"user_id": 1})]

else:
    import sqlite3
    db = sqlite3.connect("users.db", check_same_thread=False)
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    db.commit()

    def add_user(user_id):
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        db.commit()

    def remove_user(user_id):
        cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
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

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- BOT CLIENT ---
bot = Client("auto_approve_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- START ---
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    add_user(message.from_user.id)

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✨ Main Channel", url="https://t.me/Hindi_Tv_Verse"),
            InlineKeyboardButton("📢 Updates", url="https://t.me/AJ_TVSERIAL")
        ],
        [InlineKeyboardButton("🛠 Support", url="https://t.me/SerialVerse_support")]
    ])

    await message.reply_photo(
        photo=random.choice(IMG_LINKS),
        caption=START_MSG.format(name=message.from_user.first_name),
        reply_markup=buttons
    )

# --- AUTO APPROVE ---
@bot.on_chat_join_request()
async def approve_request(client, request: ChatJoinRequest):
    add_user(request.from_user.id)
    try:
        await client.approve_chat_join_request(request.chat.id, request.from_user.id)
        await client.send_photo(
            chat_id=request.from_user.id,
            photo=random.choice(IMG_LINKS),
            caption=f"<b>Hello {request.from_user.first_name} ✨,\n\nApproved!</b>"
        )
    except Exception as e:
        if "USER_ALREADY_PARTICIPANT" in str(e):
            pass
        else:
            print(e)

# --- STATS ---
@bot.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats(client, message):
    total = get_total_users()
    await message.reply_text(f"📊 Users: `{total}`")

# --- BROADCAST ---
@bot.on_message(filters.command("broadcast") & filters.user(ADMIN_ID) & filters.reply)
async def broadcast(client, message):
    users = get_all_users()
    msg = message.reply_to_message

    total = len(users)
    success = blocked = deleted = failed = 0

    status = await message.reply_text(f"🚀 Broadcasting to {total} users...")

    for i, user_id in enumerate(users):
        try:
            await msg.copy(chat_id=user_id)
            success += 1
            await asyncio.sleep(0.04)

        except FloodWait as e:
            await asyncio.sleep(e.value)

        except UserIsBlocked:
            blocked += 1
            remove_user(user_id)

        except InputUserDeactivated:
            deleted += 1
            remove_user(user_id)

        except Exception:
            failed += 1

        if (i + 1) % 100 == 0:
            try:
                await status.edit(f"📤 {i+1}/{total} Done")
            except:
                pass

    await status.edit(
        f"✅ Done!\n\n"
        f"Success: {success}\nBlocked: {blocked}\nDeleted: {deleted}\nFailed: {failed}"
    )

# --- MAIN ---
if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    print("🔥 Bot Started Successfully!")
    bot.run()
