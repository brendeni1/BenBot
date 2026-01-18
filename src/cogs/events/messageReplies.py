import discord
import random
import re
import sys
from discord.ext import commands

from src.classes import *

SINGLETON_REPLIES = {
    r"\bwe\b": ['"we" 🥀', "https://i.breia.net/DBYjGFHE.gif"],
    r"\bi guess bro\b": [
        "https://i.breia.net/DBYjGFHE.gif",
        "https://i.breia.net/4d7SohgU.png",
    ],
    r"\b(soft hands)|(blue collar)\b": ["https://i.breia.net/Cfp1aO8R.gif"],
    r"((a|i)(llah))|(\bhabibi\b)": ["https://i.breia.net/bVk0DWNA.png"],
    r"(unemploy(ed|ment))": ["https://i.breia.net/RzEbgwMN.gif"],
    r"(\bemploy(ed|ment))": ["https://i.breia.net/kjD8A4o3.gif"],
    r"hmm+": ["https://i.breia.net/ucUfSviT.gif"],
    r"(\b6|\bsix)(.*)(?=(7\b|seven\b))": [
        "https://i.breia.net/etPwz8wR.png",
        "https://i.breia.net/ZrYEByai.gif",
        "https://i.breia.net/Ff2MTS2c.gif",
        "https://i.breia.net/Jd6LOyTe.gif",
        "https://i.breia.net/JkoqRu6o.gif",
    ],
    r"\bhouse\b": [
        "https://i.breia.net/ntV3hf4i.jpg",
        "https://i.breia.net/a4e4rdVi.jpg",
        "https://i.breia.net/EadhEmsz.gif",
        "https://i.breia.net/bOaRxQFF.jpg",
        "https://i.breia.net/wzJTadQQ.jpg",
    ],
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
