import os
import random
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from pymongo import MongoClient
from config import API_ID, API_HASH, BOT_TOKEN, START_MSG, IMG_LINKS, ADMIN_ID

# --- MONGODB SETUP ---
MONGO_DB_URI = os.environ.get("MONGO_DB_URI")
mongo_client = MongoClient(MONGO_DB_URI)
db = mongo_client["telegram_bot"]
users_col = db["users"]

def add_user(user_id):
    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id}},
        upsert=True
    )

def remove_user(user_id):
    users_col.delete_one({"user_id": user_id})

def get_total_users():
    return users_col.count_documents({})

def get_all_users():
    return [user["user_id"] for user in users_col.find({}, {"user_id": 1})]

# --- HEALTH CHECK SERVER ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running")

    def do_HEAD(self):  # 🔥 FIXED
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

# --- AUTO APPROVE ---
@bot.on_chat_join_request()
async def approve_request(client, request: ChatJoinRequest):
    add_user(request.from_user.id)
    try:
        await client.approve_chat_join_request(request.chat.id, request.from_user.id)
        await client.send_photo(
            chat_id=request.from_user.id,
            photo=random.choice(IMG_LINKS),
            caption=f"<b>Hello {request.from_user.first_name} ✨,\n\nYour request has been approved!</b>\n\nJoin: @Hindi_Tv_Verse & @AJ_TVSERIAL"
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
    await message.reply_text(f"📊 Total Users: `{total}`")

# --- FAST + SAFE BROADCAST ---
@bot.on_message(filters.command("broadcast") & filters.user(ADMIN_ID) & filters.reply)
async def broadcast(client, message):
    users = get_all_users()
    msg = message.reply_to_message

    total = len(users)
    success = blocked = deleted = failed = 0

    status = await message.reply_text(f"🚀 Broadcast Started...\n👥 Users: {total}")

    for i, user_id in enumerate(users):
        try:
            await msg.copy(chat_id=user_id)
            success += 1
            await asyncio.sleep(0.04)  # 🔥 optimized speed

        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                await msg.copy(chat_id=user_id)
                success += 1
            except:
                failed += 1

        except UserIsBlocked:
            blocked += 1
            remove_user(user_id)

        except InputUserDeactivated:
            deleted += 1
            remove_user(user_id)

        except Exception as e:
            failed += 1

        # 🔄 Update every 100 users (better UX)
        if (i + 1) % 100 == 0:
            try:
                await status.edit(
                    f"📤 Broadcasting...\n\n"
                    f"Done: {i+1}/{total}\n"
                    f"✅ Success: {success}\n"
                    f"🚫 Blocked: {blocked}\n"
                    f"💀 Deleted: {deleted}\n"
                    f"❌ Failed: {failed}"
                )
            except:
                pass

    await status.edit(
        f"✅ Broadcast Completed!\n\n"
        f"👥 Total: {total}\n"
        f"✨ Success: {success}\n"
        f"🚫 Blocked: {blocked}\n"
        f"💀 Deleted: {deleted}\n"
        f"❌ Failed: {failed}"
    )

# --- MAIN ---
if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    print("🔥 Bot Started Successfully!")
    bot.run()
