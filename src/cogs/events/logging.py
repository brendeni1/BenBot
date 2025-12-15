import discord
import sys
from discord.ext import commands

from src.classes import *

from src.utils.logging import commandLogs, messageLogs
from src.utils import dates


class CommandLogging(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Command logging cog."

    @commands.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext):
        logEntryObj = commandLogs.contextToLogEntry(ctx)

        commandLogs.insertLogEntry(logEntryObj)


class MessageLogging(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Chat message logging cog."

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        logEntryObj = messageLogs.messageToLogEntryObj(msg, self.bot)

        logEntryObj.writeToDB()


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
