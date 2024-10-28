import qbittorrentapi
from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
from config import *


# Configure qBittorrent client connection
qbt_conn_info = dict(
    host="localhost",
    port=8080,
    username="admin",
    password="adminadmin",
)

qbt_client = qbittorrentapi.Client(**qbt_conn_info)

# Log in to qBittorrent
try:
    qbt_client.auth_log_in()
except qbittorrentapi.LoginFailed as e:
    print(f"Login failed: {e}")

# Initialize Pyrogram client
bot = Client(
    name="NexusDL-bot",
    api_hash=API_HASH,
    api_id=API_ID,
    bot_token=BOT_TOKEN,
    workers=30
)
# Dictionary to track who added each torrent
user_torrent_map = {}

# Track completed torrents to avoid duplicate notifications
completed_torrents = set()

async def check_completed_torrents():
    """Periodically check for completed torrents and send notifications."""
    while True:
        try:
            torrents = qbt_client.torrents_info()
            for torrent in torrents:
                if torrent.state == "completed" and torrent.hash not in completed_torrents:
                    completed_torrents.add(torrent.hash)
                    # Notify the user who added this torrent
                    user_id = user_torrent_map.get(torrent.hash)
                    if user_id:
                        await bot.send_message(user_id, f"Download completed: {torrent.name}")
        except Exception as e:
            print(f"Error checking torrents: {e}")
        
        # Check every 30 seconds
        await asyncio.sleep(30)

@bot.on_message(filters.command("add"))
async def add_torrent(client, message: Message):
    if len(message.command) < 2:
        await message.reply("Please provide a torrent URL or magnet link.")
        return
    
    url = message.command[1]
    try:
        response = qbt_client.torrents_add(urls=url)
        if response == "Ok.":
            await message.reply("Torrent added successfully!")
            # Store the user_id and torrent hash
            torrents = qbt_client.torrents_info()
            for torrent in torrents:
                if torrent.state == "downloading" and torrent.hash not in user_torrent_map:
                    user_torrent_map[torrent.hash] = message.from_user.id
        else:
            await message.reply("Failed to add torrent.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@bot.on_message(filters.command("list"))
async def list_torrents(client, message: Message):
    torrents = qbt_client.torrents_info()
    if not torrents:
        await message.reply("No torrents found.")
        return
    
    msg = "Torrents:\n"
    for torrent in torrents:
        msg += f"{torrent.hash[-6:]}: {torrent.name} ({torrent.state})\n"
    
    await message.reply(msg)

@bot.on_message(filters.command("stop"))
async def stop_torrents(client, message: Message):
    try:
        qbt_client.torrents_stop.all()
        await message.reply("All torrents have been stopped.")
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@bot.on_message(filters.command("info"))
async def qbittorrent_info(client, message: Message):
    try:
        info = f"qBittorrent: {qbt_client.app.version}\n"
        info += f"qBittorrent Web API: {qbt_client.app.web_api_version}\n"
        info += "Build Info:\n"
        for k, v in qbt_client.app.build_info.items():
            info += f"{k}: {v}\n"
        
        await message.reply(info)
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

# Start the completed torrents checker in the background when bot starts
@bot.on_start
async def start_background_tasks(client):
    asyncio.create_task(check_completed_torrents())

# Run the bot
bot.run()
