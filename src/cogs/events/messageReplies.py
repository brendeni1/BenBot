import discord
import random
import re
import sys
from discord.ext import commands

from src.classes import *

SINGLETON_REPLIES = {
    r"\bwe\b": ['"we" 🥀', "https://i.breia.net/DBYjGFHE.gif"],
    r"\bi guess bro\b": ["https://i.breia.net/DBYjGFHE.gif"],
    r"\b(soft hands)|(blue collar)\b": ["https://i.breia.net/Cfp1aO8R.gif"],
    r"(a|i)(llah)": ["https://i.breia.net/bVk0DWNA.png"],
    r"(unemployed)": ["https://i.breia.net/RzEbgwMN.gif"],
    r"(\bemployed)": ["https://i.breia.net/kjD8A4o3.gif"],
}


class SingletonRepliesCog(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Fun replies to single message events that match regexs."

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.content and self.bot.user.id != msg.author.id:
            concatenatedReply = ""

            for regexStr, replyStrs in SINGLETON_REPLIES.items():
                if re.findall(
                    pattern=regexStr, string=msg.content, flags=re.IGNORECASE
                ):
                    chosenReply = random.choice(replyStrs)

                    concatenatedReply += chosenReply + "\n"

            if concatenatedReply:
                await msg.reply(content=concatenatedReply)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
