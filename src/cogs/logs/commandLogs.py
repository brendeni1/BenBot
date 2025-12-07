import discord
import sys
from discord.ext import commands

from src.classes import *

from src.utils.logging import commandLogs
from src.utils import dates


class CommandLogging(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Command logging cog."

    @commands.Cog.listener()
    async def on_application_command(self, ctx):
        logEntryObj = commandLogs.contextToLogEntry(ctx)

        commandLogs.insertLogEntry(logEntryObj)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
