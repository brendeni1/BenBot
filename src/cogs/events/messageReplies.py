import discord
import random
import re
import sys
from discord.ext import commands

from src.classes import *
from src.errors import *
from src import constants

SINGLETON_REPLIES = {
    r"\bwe\b": ['"we" 🥀', "https://files.brendenian.net/BRNDN/dbyjgfhe.gif"],
    r"(\bi guess bro\b)|(\bigb\b)": [
        "https://files.brendenian.net/BRNDN/dbyjgfhe.gif",
    ],
    r"\b(soft hands)|(blue collar)\b": ["https://files.brendenian.net/BRNDN/cfp1ao8r.gif"],
    r"((a|i)(llah))|(\bhabibi\b)": ["https://files.brendenian.net/BRNDN/bvk0dwna.png"],
    r"(unemploy(ed|ment))": ["https://files.brendenian.net/BRNDN/rzebgwmn.gif"],
    r"(\bemploy(ed|ment))": ["https://files.brendenian.net/BRNDN/kjd8a4o3.gif"],
    r"hmm+": ["https://files.brendenian.net/BRNDN/ucufsvit.gif"],
    r"(\b6|\bsix)(.*)(?=(7\b|seven\b))": [
        "https://files.brendenian.net/BRNDN/etpwz8wr.png",
        "https://files.brendenian.net/BRNDN/zryebyai.gif",
        "https://files.brendenian.net/BRNDN/ff2mts2c.gif",
        "https://files.brendenian.net/BRNDN/jd6loyte.gif",
        "https://files.brendenian.net/BRNDN/jkoqru6o.gif",
    ],
    r"(\bcuddy\b)": [
        "https://files.brendenian.net/BRNDN/2hkenbag.jpg",
        "https://files.brendenian.net/BRNDN/itf0kcbz.png",
    ],
    r"(\bwilson\b)|(\bi too am in this episode\b)": [
        "https://files.brendenian.net/BRNDN/qmd7ylej.jpg",
        "https://files.brendenian.net/BRNDN/gkgybi8o.jpg",
    ],
    r"(\bforeman\b)|(\bvexes\b)": [
        "https://files.brendenian.net/BRNDN/e8b0syfl.png",
        "https://files.brendenian.net/BRNDN/pxwlpeqf.png",
    ],
    r"\bhouse\b": [
        "https://files.brendenian.net/BRNDN/ntv3hf4i.jpg",
        "https://files.brendenian.net/BRNDN/a4e4rdvi.jpg",
        "https://files.brendenian.net/BRNDN/eadhemsz.gif",
        "https://files.brendenian.net/BRNDN/boarxqff.jpg",
        "https://files.brendenian.net/BRNDN/wzjtadqq.jpg",
    ],
    r"\blego man\b": [
        "https://files.brendenian.net/BRNDN/jeyr8ysh.gif",
    ],
    r"\b(tory)|(mckay)\b": [
        "https://files.brendenian.net/BRNDN/cliznyth.png",
        "https://files.brendenian.net/BRNDN/61AXf5.png",
        "https://files.brendenian.net/BRNDN/H8v1zH.png",
    ]
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


class CommandRoleCatcher(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Replies to people when a command is restricted."

    @commands.Cog.listener()
    async def on_application_command_error(
        self, ctx: discord.ApplicationContext, e: discord.DiscordException
    ):
        if isinstance(e, CommandUnderConstruction):
            reply = constants.UNDER_CONSTRUCTION_EMBED

            await reply.send(ctx)
        elif isinstance(e, CommandOwnerOnly):
            reply = constants.OWNER_ONLY_EMBED

            await reply.send(ctx)
        else:
            raise e


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
