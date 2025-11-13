import discord
import sys
from discord.ext import commands

from src.classes import *

from src.utils import movies


class Movies(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Commands for looking up movies and showtimes."

    movies = discord.SlashCommandGroup(
        name="movies",
        description="Commands for looking up details about movies.",
        guild_ids=[799341195109203998],
    )

    @movies.command(
        description="Look up showtimes for movies.", guild_ids=[799341195109203998]
    )
    async def showtimes(self, ctx: discord.ApplicationContext):
        await ctx.respond(movies.test())


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
