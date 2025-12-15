import discord
import re
import sys
from discord.ext import commands

from src.classes import *

SINGLETON_REPLIES = {r"(?=.*\bhow\b)(?=.*\bwe\b)": '"we" 🥀'}


class SingletonRepliesCog(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Fun replies to single message events that match regexs."

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.content:
            concatenatedReply = ""

            for regexStr, replyStr in SINGLETON_REPLIES.items():
                if re.findall(
                    pattern=regexStr, string=msg.content, flags=re.IGNORECASE
                ):
                    concatenatedReply += replyStr + "\n"

            if concatenatedReply:
                await msg.reply(content=concatenatedReply)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
