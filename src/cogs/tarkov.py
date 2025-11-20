import discord
import sys
from discord.ext import commands

from src.classes import *
from src.utils import tarkov

ITEM_SEARCH_QUERY_RETURN_LIMIT = 10


class TarkovItemCommands(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Commands for looking up items in Escape from Tarkov."

    tarkovCommands = discord.SlashCommandGroup(
        name="tarkov",
        description="Commands for interacting with data from Escape from Tarkov.",
        guild_ids=[799341195109203998],
    )

    itemCommands = tarkovCommands.create_subgroup(
        name="items",
        description="Commands for looking up items in Escape from Tarkov.",
        guild_ids=[799341195109203998],
    )

    @itemCommands.command(
        description="Search for an item by name or tarkov.dev ID.",
        guild_ids=[799341195109203998],
    )
    async def search(self, ctx: discord.ApplicationContext, term: discord.Option(str, description="An in-game item to search for.", required=True), id: discord.Option(bool, description="Whether the item provided is an ID. (Must be a tarkov.dev ID)", default=False)):  # type: ignore
        try:
            await ctx.defer()

            searchKey = "ids" if id else "names"

            query = f'{{ items({searchKey}: ["{term}"], limit: {ITEM_SEARCH_QUERY_RETURN_LIMIT}) {{ id, name }} }}'

            queryResponse = tarkov.fetch(query=query)

            await ctx.followup.send(str(queryResponse), ephemeral=True)
        except Exception as e:
            raise e
            reply = EmbedReply(
                "Tarkov - Item Search - Error",
                "tarkov",
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
