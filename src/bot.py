import discord

class Bot(discord.Bot):
    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(name="/commands", type=discord.ActivityType.listening))

        print(f"Logged in as {self.user}!")