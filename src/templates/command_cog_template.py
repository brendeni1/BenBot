import discord
import sys
from discord.ext import commands

from src.classes import *


class MyCog(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Template for cogs."

    @discord.slash_command(
        description="Template for commands.", guild_ids=[799341195109203998]
    )
    async def command(self, ctx: discord.ApplicationContext):
        try:
            pass
        except Exception as e:
            reply = EmbedReply("- - Error", "", error=True, description=f"Error: {e}")

            await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
