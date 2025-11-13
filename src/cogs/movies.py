import discord
import sys
from discord.ext import commands

from src.classes import *

from src import constants

from src.utils import movies

CINEMAS = movies.listCinemaLocations()

DEFAULT_CHAIN = "Landmark"
DEFAULT_PROVINCE = "ON"
DEFAULT_LOCATION = "Windsor"


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
    async def showtimes(
        self,
        ctx: discord.ApplicationContext,
        chain: discord.Option(
            input_type=str,
            description="Select which chain of cinema to use.",
            autocomplete=True,
        ),  # type: ignore
        province: discord.Option(
            input_type=str,
            description="Select which province to look up cinemas.",
            autocomplete=True,
        ),  # type: ignore
        location: discord.Option(
            input_type=str,
            description="Select which cinema location to view.",
            autocomplete=True,
        ),  # type: ignore
    ):
        try:
            chain = chain or DEFAULT_CHAIN
            province = province or DEFAULT_PROVINCE
            location = location or DEFAULT_LOCATION

            await ctx.respond(f"You picked **{chain} → {province} → {location}**")
        except Exception as e:
            reply = EmbedReply(
                "Movie Showtimes - Error", "movies", True, description=f"Error: {e}"
            )

            await reply.send(ctx)

    @movies.showtimes.autocomplete("province")
    async def provinceAutocomplete(ctx: discord.AutocompleteContext):
        provinces = list(constants.MOVIE_CINEMAS["Landmark"].keys())
        query = ctx.value.lower()

        return [province for province in provinces if query in province.lower()][:25]


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
