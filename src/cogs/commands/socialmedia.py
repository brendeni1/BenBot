import discord
import sys
from discord.ext import commands

from src.classes import *


class InstagramCommands(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Commands for fetching Instagram data."

    instagramCommandsGroup = discord.SlashCommandGroup(
        name="instagram",
        description="Commands for fetching Instagram data.",
        guild_ids=[799341195109203998],
    )

    @instagramCommandsGroup.command(
        description="Template for commands.", guild_ids=[799341195109203998]
    )
    async def latest(
        self,
        ctx: discord.ApplicationContext,
        username: discord.Option(
            "str", description="The Instagram username to fetch posts for."
        ),  # type: ignore
    ):
        await ctx.defer()

        try:
            pass
        except Exception as e:
            reply = EmbedReply(
                "Instagram - Latest - Error", "", error=True, description=f"Error: {e}"
            )

            await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
