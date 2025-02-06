import discord

class Bot(discord.Bot):
    async def on_ready(self):
        print(f"Logged in as {self.user}!")