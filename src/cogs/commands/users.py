import discord
import sys
from discord.ext import commands

from src.classes import *


class Users(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Collection of commands for Discord users."

    @discord.slash_command(
        description="Get a user's avatar.", guild_ids=[799341195109203998]
    )
    async def avatar(
        self,
        ctx: discord.ApplicationContext,
        target: discord.Option(
            discord.Member,
            description="Optional target user. Defaults to invoker.",
            required=False,
        ),  # type: ignore
        use_guild_avatar: discord.Option(
            bool,
            description="Should the Guild's avatar be pulled instead of global?",
            default=True,
        ),  # type: ignore
    ):
        try:
            target: discord.Member = ctx.user if not target else target

            targetPFP = (
                target.display_avatar
                if ctx.guild and use_guild_avatar
                else target.avatar
            )

            if not targetPFP:
                raise Exception("Error parsing out user's profile picture.")

            reply = EmbedReply(
                "Users - Avatar", "users", description=f"Avatar for {target.mention}"
            )

            reply.set_image(url=targetPFP.url)

            await reply.send(ctx)
        except Exception as e:
            reply = EmbedReply(
                "Users - Avatar - Error", "users", error=True, description=f"Error: {e}"
            )

            await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
