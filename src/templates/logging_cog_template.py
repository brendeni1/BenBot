import discord
import sys
from discord.ext import commands

from src.classes import *

from src.utils.logging import commandLogs  # Change to specific log.


async def parseLogEntry(
    ctx: discord.ApplicationContext,
) -> commandLogs.LogEntry:  # Change to specific log.
    pass


async def insertLogEntry(entry: commandLogs.LogEntry):  # Change to specific log.
    pass


class Logging(commandLogs.Cog):  # Change to specific log.
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "<> logging cog."  # Change to specific log.


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
