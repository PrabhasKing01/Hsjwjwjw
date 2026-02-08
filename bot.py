import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from config import API_ID, API_HASH, BOT_TOKEN, START_MSG, IMG_LINKS, ADMIN_ID

bot = Client(
    "my_advance_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Start Command
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

# Auto Approve Join Request
@bot.on_chat_join_request()
async def approve_request(client, request: ChatJoinRequest):
    try:
        # Approve the request
        await client.approve_chat_join_request(request.chat.id, request.from_user.id)
        
        # Send a welcome message in DM
        welcome_dm = f"<b>ʜᴇʟʟᴏ {request.from_user.first_name} ✨,\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ ʜᴀs ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>"
        await client.send_photo(
            chat_id=request.from_user.id,
            photo=random.choice(IMG_LINKS),
            caption=welcome_dm
        )
        
        # Notify Admin (Optional)
        await client.send_message(ADMIN_ID, f"🔔 New Member Approved: {request.from_user.first_name}")
        
    except Exception as e:
        print(f"Error: {e}")

print("🔥 Bot is running on Advance Pyrogram Engine!")
bot.run()

