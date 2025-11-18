import discord
from src.utils import music
from src.cogs import antiben


class Bot(discord.Bot):
    async def on_ready(self):
        await self.change_presence(
            activity=discord.Activity(
                name="/commands", type=discord.ActivityType.listening
            )
        )

        self.add_view(music.FinishedRatingPersistentMessageButtonsView())
        print("Persistent album rating buttons loaded.")

        self.add_view(antiben.AntiBenMovementView())
        print("Persistent Anti-Ben buttons loaded.")

        print(f"Logged in as {self.user}!")
