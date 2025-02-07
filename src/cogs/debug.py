import discord
import time
import sys
from discord.ext import commands

from src.utils import dates
from src.classes import AppReply

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Contains a few debug and bot vital commands."
        self.timeStarted = time.time()
    
    @discord.slash_command(description = "Returns a list of vitals such as latency and uptime.", guild_ids=[799341195109203998])
    async def ping(self, ctx):
        uptime = dates.formatSeconds(round(time.time() - self.timeStarted))
        latency = round(self.bot.latency * 1000)

        reply = AppReply(
            True,
            f"<:zamn:1089027418959904809> Pong! Latency: {latency}ms. Uptime: {uptime}. For a list of commands and a short description, use '/commands'. Source code: https://github.com/brendeni1/BenBot"
        )

        await reply.sendReply(ctx)
    
    @discord.slash_command(description = "Returns a list of commands.", guild_ids=[799341195109203998])
    async def commands(self, ctx):
        cogs = self.bot.cogs

        commandGroups = [((cogs.get(cog)).get_commands()) for cog in cogs]

        prettyCommands = []

        for commandGroup in commandGroups:
            for command in commandGroup:
                prettyCommands.append(f"/{command.name} - {command.description}")

        prettyCommands.sort()
        
        reply = AppReply(
            True,
            f'A list of commands:\n\n{"\n".join(prettyCommands)}\n\nUse the command to see available parameters.'
        )

        await reply.sendReply(ctx)

def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)
        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            bot.add_cog(obj(bot))