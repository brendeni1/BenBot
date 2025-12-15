import discord
import sys
from discord.ext import commands

from src.classes import *

from src.utils import dates

import telethon
from io import BytesIO

TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")
TELEGRAM_PASSWORD = os.getenv("TELEGRAM_PASSWORD")

CHAT_IDS = [2487799389, 1960735023]

DB_TABLE_NAME = "taylortracker"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(CURRENT_DIR, '..', 'temp')

class TaylorTracker(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot
        
        self.description = "Sends updates on the status of Taylor's jet. Use /data add table:taylortracker."

        self.telegramClient = telethon.TelegramClient(
            "taylortracker",
            TELEGRAM_API_ID,
            TELEGRAM_API_HASH
        )

        self.telegramClient.loop.run_until_complete(self.tracker())

    def uploadImage(self, path) -> discord.File:
        if path:
            with open(path, "rb") as media:
                data = media.read()
            upload = discord.File(BytesIO(data), filename=os.path.basename(path))
            return upload
        else:
            return None
    
    async def newMessageInTrackerChat(self, event):
        msg: telethon.types.Message = event.message

        sender: telethon.types.Channel = await msg.get_sender()

        if sender.id not in CHAT_IDS:
            return
        
        database = LocalDatabase()

        channelsToSendTo = database.get(f"SELECT receivingChannel FROM {DB_TABLE_NAME}")

        if not channelsToSendTo:
            return
        
        telegramMedia = await msg.download_media(TEMP_DIR)

        uploadedMedia = self.uploadImage(telegramMedia)

        action = "Departure" if "Took off" in msg.message else "Arrival" if "Landed" in msg.message else "Circling" if "Circling" in msg.message else "Other"

        reply = EmbedReply(f"Taylor Swift Tracker - {action}", "taylortracker")

        if telegramMedia:
            telegramMediaFilename = os.path.basename(telegramMedia)
        
            reply.set_image(url=f"attachment://{telegramMediaFilename}")
        
        reply.description = msg.message if msg.message else "No Message"

        reply.set_footer(text=f"{dates.formatSimpleDate(msg.date) if msg.date else "N/D"} UTC · t.me/s/TSwiftJets")

        for channelToSendTo in channelsToSendTo:
            channel = self.bot.get_channel(channelToSendTo[0])

            if channel:
                await channel.send(embed=reply, file=uploadedMedia)

        if telegramMedia:
            os.remove(telegramMedia)

    async def tracker(self):
        try:
            await self.telegramClient.start(
                TELEGRAM_PHONE,
                TELEGRAM_PASSWORD
            )
        except Exception as e:
            self.telegramClient = None
            
            raise e
        
        if self.telegramClient:            
            self.telegramClient.add_event_handler(self.newMessageInTrackerChat, telethon.events.NewMessage)

def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))