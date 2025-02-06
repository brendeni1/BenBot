import discord
import time
import datetime
from discord.ext import commands

from src.utils import dates

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Contains a few debug and bot vital commands."
        self.timeStarted = time.time()
    
    @discord.slash_command(description = "Returns a list of vitals such as latency and uptime.", guild_ids=[799341195109203998])
    async def ping(self, ctx):
        uptime = round(time.time() - self.timeStarted)

        await ctx.respond(f"<:zamn:1089027418959904809> Pong! Latency: {round(self.bot.latency * 1000)}ms. Uptime: {dates.formatSeconds(uptime)}. For a list of commands and a short description, use '/commands'.")
    
    @discord.slash_command(description = "Returns a list of commands.", guild_ids=[799341195109203998])
    async def commands(self, ctx):
        cogs = self.bot.cogs

        commandGroups = [((cogs.get(cog)).get_commands()) for cog in cogs]

        prettyCommands = []

        for commandGroup in commandGroups:
            for command in commandGroup:
                prettyCommands.append(f"/{command.name} - {command.description}")

        await ctx.respond("\n".join(prettyCommands))

def setup(bot):
    bot.add_cog(Debug(bot))