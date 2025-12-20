import discord
from src.utils import music, imagesCog
from src.cogs.commands import antiben


class Bot(discord.Bot):
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
