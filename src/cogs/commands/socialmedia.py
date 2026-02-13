import discord
import sys
from discord.ext import commands

from src.classes import *
from src.utils import socialmedia


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
        description="Fetch a user's latest Instagram posts by username.",
        guild_ids=[799341195109203998],
    )
    async def latest(
        self,
        ctx: discord.ApplicationContext,
        username: discord.Option(
            str, description="The Instagram username to fetch posts for."
        ),  # type: ignore
    ):
        await ctx.defer()

        try:
            fetchedPosts = await socialmedia.fetchInstagramPosts(username=username)

            paginatedPosts = socialmedia.InstagramPaginator(fetchedPosts)

            await paginatedPosts.respond(ctx.interaction)
        except Exception as e:
            reply = EmbedReply(
                "Instagram - Latest - Error",
                "socialmedia",
                error=True,
                description=f"Error: {e}",
            )

            await reply.send(ctx)

    @instagramCommandsGroup.command(
        description="Fetch Caffeinated Collective's latest Instagram posts.",
        guild_ids=[799341195109203998],
    )
    async def cc(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        try:
            fetchedPosts = await socialmedia.fetchInstagramPosts(
                username="caffeinatedcollectivee"
            )

            paginatedPosts = socialmedia.InstagramPaginator(fetchedPosts)

            await paginatedPosts.respond(ctx.interaction)
        except Exception as e:
            raise e
            reply = EmbedReply(
                "Instagram - Latest (CC) - Error",
                "socialmedia",
                error=True,
                description=f"Error: {e}",
            )

            await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
