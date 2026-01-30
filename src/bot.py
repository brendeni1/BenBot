import os
import aiohttp
import discord

from discord.ext import tasks
from src.utils import music, imagesCog
from src.cogs.commands import antiben


class Bot(discord.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kuma_heartbeat.start()

    @tasks.loop(seconds=60)
    async def kuma_heartbeat(self):
        push_url = os.getenv("KUMA_PUSH_URL")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(push_url) as response:
                    if response.status == 200:
                        # Heartbeat successful
                        pass
        except Exception as e:
            print(f"Uptime Kuma heartbeat failed: {e}")

    @kuma_heartbeat.before_loop
    async def before_heartbeat(self):
        await self.wait_until_ready()

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Activity(
                name="/commands", type=discord.ActivityType.watching
            )
        )

        self.add_view(music.FinishedRatingPersistentMessageButtonsView())
        print("Persistent Album Rating buttons loaded.")

        self.add_view(antiben.AntiBenMovementView())
        print("Persistent Anti-Ben buttons loaded.")

        self.add_view(imagesCog.ImageView(None))
        print("Persistent Image buttons loaded.")

        print(f"Logged in as {self.user}!")
