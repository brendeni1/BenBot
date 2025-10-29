import discord
import psutil
import time
import sys
from discord.ext import commands

from src.utils import dates

from src.classes import *

class Debug(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot = bot
        
        self.description = "Contains a few debug and bot vital commands."
        self.timeStarted = time.time()
    
    @discord.slash_command(description = "Returns a list of vitals such as latency and uptime.", guild_ids=[799341195109203998])
    async def ping(self, ctx):
        uptime = dates.formatSeconds(round(time.time() - self.timeStarted))
        latency = round(self.bot.latency * 1000)
        cpuUsage = psutil.cpu_percent(interval=1)

        formatted = f"<:sus:816524395605786624>  Pong! Latency: {latency}ms. Uptime: {uptime}. CPU Usage: {cpuUsage}%.\n\nFor a list of commands and a short description, use '/commands'.\n\nSource code: https://github.com/brendeni1/BenBot"

        reply = EmbedReply("Ping", "debug", description=formatted)

        await reply.send(ctx)
    
    @discord.slash_command(description = "Returns a list of commands.", guild_ids=[799341195109203998])
    async def commands(self, ctx):
        cogs = self.bot.cogs

        commandGroups = [((cogs.get(cog)).get_commands()) for cog in cogs]

        prettyCommands = []

        for commandGroup in commandGroups:
            for command in commandGroup:
                prettyCommands.append(f"/{command.name} - {command.description}")

        prettyCommands.sort()

        formatted = f'A list of commands:\n\n{"\n".join(prettyCommands)}'

        reply = EmbedReply("Commands", "debug", description=formatted)

        reply.set_footer(text="Use the command to see available parameters.")

        await reply.send(ctx)

def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))