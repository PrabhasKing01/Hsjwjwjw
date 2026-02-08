import os
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from config import API_ID, API_HASH, BOT_TOKEN, START_MSG, IMG_LINKS, ADMIN_ID

# --- YEH HAI PORT WALA CODE (KOYEB FIX) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running")

def run_health_server():
    # Koyeb 8000 port mangta hai, hum wahi de rahe hain
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health Check Server started on port {port}")
    server.serve_forever()
# ----------------------------------------

bot = Client(
    "my_advance_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user = message.from_user
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
        caption=START_MSG.format(name=user.first_name),
        reply_markup=buttons
    )

@bot.on_chat_join_request()
async def approve_request(client, request: ChatJoinRequest):
    try:
        await client.approve_chat_join_request(request.chat.id, request.from_user.id)
        await client.send_photo(
            chat_id=request.from_user.id,
            photo=random.choice(IMG_LINKS),
            caption=f"<b>ʜᴇʟʟᴏ {request.from_user.first_name} ✨,\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ ʜᴀs ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>"
        )
    except Exception as e:
        print(f"Error: {e}")

# --- MAIN RUN BLOCK ---
if __name__ == "__main__":
    # Port wala server thread mein chalana zaroori hai
    threading.Thread(target=run_health_server, daemon=True).start()
    
    print("🔥 Bot is starting...")
    bot.run()
